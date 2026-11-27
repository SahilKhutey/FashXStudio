"""Consent-checked, idempotent feedback event ingestion service (Task 8.5.11)."""

from __future__ import annotations

from datetime import UTC, datetime

from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.contracts import FeedbackEventRequest
from fashx.feedback.idempotency import (
    FeedbackConflict,
    canonical_payload_hash,
    validate_occurred_at,
)
from fashx.feedback.registry import EVENT_REGISTRY
from fashx.feedback.repository import InMemoryFeedbackRepository, StoredFeedbackEvent


class FeedbackIngestionService:
    """Validates, consent-checks, deduplicates, and durably records feedback events."""

    def __init__(
        self,
        *,
        repository: InMemoryFeedbackRepository,
        consent_service: FeedbackConsentService,
    ) -> None:
        self.repository = repository
        self.consent_service = consent_service

    def ingest(
        self,
        *,
        shopper_id: str,
        request: FeedbackEventRequest,
        allow_server_only: bool = False,
    ) -> tuple[StoredFeedbackEvent, bool]:
        """Ingest a feedback event and return ``(record, deduplicated)``."""
        spec = EVENT_REGISTRY.get(request.event_type)
        if spec is None:
            raise ValueError(f"Unsupported feedback event type: {request.event_type}")
        if spec.server_only and not allow_server_only:
            raise PermissionError(
                f"Event '{request.event_type}' can only be emitted by authoritative server services"
            )
        if request.subject_type != spec.subject_type:
            raise ValueError(
                f"Invalid subject_type '{request.subject_type}' for '{request.event_type}'"
            )

        if not self.consent_service.can_collect(
            shopper_id=shopper_id,
            purpose=spec.consent_purpose,
            event_type=request.event_type,
        ):
            raise PermissionError(
                f"Shopper has not granted consent for {spec.consent_purpose.value}"
            )

        if (
            self.repository.valid_products is not None
            and spec.subject_type == "PRODUCT"
            and request.subject_id not in self.repository.valid_products
        ):
            raise ValueError(f"Unknown product '{request.subject_id}'")

        if spec.subject_type == "VTO_JOB" and request.subject_id in self.repository.vto_job_owners:
            if self.repository.vto_job_owners[request.subject_id] != shopper_id:
                raise PermissionError("VTO job does not belong to authenticated shopper")

        occurred_utc = validate_occurred_at(request.occurred_at)
        payload = request.model_dump(mode="json")
        payload_hash = canonical_payload_hash(payload)

        existing = self.repository.get_by_event_id(request.event_id)
        if existing is not None:
            if existing.shopper_id != shopper_id:
                raise FeedbackConflict("Event ID belongs to another shopper")
            if existing.payload_hash != payload_hash:
                raise FeedbackConflict("Event ID reused with different payload")
            return existing, True

        consent_rev = self.consent_service.get_revision(shopper_id, spec.consent_purpose)
        rec = self.repository.create_event_and_outbox(
            event_id=request.event_id,
            shopper_id=shopper_id,
            event_type=request.event_type,
            feedback_class=spec.feedback_class.value,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            occurred_at=occurred_utc,
            received_at=datetime.now(UTC),
            source=request.source,
            session_id=request.session_id,
            context=request.context,
            consent_revision=consent_rev,
            schema_version=request.schema_version,
            payload_hash=payload_hash,
        )
        return rec, False
