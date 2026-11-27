"""Idempotent feedback outbox processor & projection builder (Phase 08.5)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.enums import FeedbackEventType, ReactionState
from fashx.feedback.registry import EVENT_REGISTRY
from fashx.feedback.repository import (
    InMemoryFeedbackRepository,
    ProductInteractionStats,
    ProductReactionProjection,
    SavedProductProjection,
    StoredFeedbackEvent,
)


class FeedbackProcessor:
    """Consumes accepted events and updates current-state projections idempotently."""

    def __init__(
        self,
        *,
        repository: InMemoryFeedbackRepository,
        consent_service: FeedbackConsentService,
    ) -> None:
        self.repository = repository
        self.consent_service = consent_service

    def process_event(self, event_id: UUID) -> str:
        """Process a single event once; returns status string."""
        event = self.repository.get_by_event_id(event_id)
        if event is None:
            return "NOT_FOUND"

        ledger = self.repository.processing.get(event_id)
        if ledger and ledger.status == "PROCESSED":
            return "ALREADY_PROCESSED"

        spec = EVENT_REGISTRY.get(event.event_type)
        if spec is None:
            if ledger:
                ledger.status = "DEAD_LETTERED"
                ledger.last_error_code = "UNSUPPORTED_EVENT"
            event.processing_status = "DEAD_LETTERED"
            return "DEAD_LETTERED"

        if not self.consent_service.can_process_existing_event(
            shopper_id=event.shopper_id,
            purpose=spec.consent_purpose,
        ):
            if ledger:
                ledger.status = "SKIPPED"
                ledger.last_error_code = "CONSENT_NOT_ACTIVE"
            event.processing_status = "SKIPPED"
            return "SKIPPED"

        self._apply_projection(event)
        now = datetime.now(UTC)
        if ledger:
            ledger.attempts += 1
            ledger.status = "PROCESSED"
            ledger.processed_at = now
        event.processed_at = now
        event.processing_status = "PROCESSED"
        return "PROCESSED"

    def _apply_projection(self, event: StoredFeedbackEvent) -> None:
        key = (event.shopper_id, event.subject_id)
        now = datetime.now(UTC)
        et = event.event_type

        if et == FeedbackEventType.PRODUCT_LIKED.value:
            self._set_reaction(event.shopper_id, event.subject_id, ReactionState.LIKE, event.event_id, now)
        elif et == FeedbackEventType.PRODUCT_DISLIKED.value:
            self._set_reaction(event.shopper_id, event.subject_id, ReactionState.DISLIKE, event.event_id, now)
        elif et in (
            FeedbackEventType.PRODUCT_LIKE_REMOVED.value,
            FeedbackEventType.PRODUCT_DISLIKE_REMOVED.value,
        ):
            self._set_reaction(event.shopper_id, event.subject_id, ReactionState.NONE, event.event_id, now)
        elif et == FeedbackEventType.PRODUCT_SAVED.value:
            offer_id = event.context.get("merchant_offer_id")
            prev = self.repository.saved.get(key)
            self.repository.saved[key] = SavedProductProjection(
                shopper_id=event.shopper_id,
                product_id=event.subject_id,
                merchant_offer_id=str(offer_id) if offer_id else (prev.merchant_offer_id if prev else None),
                is_saved=True,
                source_event_id=event.event_id,
                saved_at=prev.saved_at if prev and prev.saved_at else now,
                updated_at=now,
            )
            self.repository.bump_revision(event.shopper_id)
        elif et == FeedbackEventType.PRODUCT_UNSAVED.value:
            prev = self.repository.saved.get(key)
            self.repository.saved[key] = SavedProductProjection(
                shopper_id=event.shopper_id,
                product_id=event.subject_id,
                merchant_offer_id=prev.merchant_offer_id if prev else None,
                is_saved=False,
                source_event_id=event.event_id,
                saved_at=prev.saved_at if prev else None,
                updated_at=now,
            )
            self.repository.bump_revision(event.shopper_id)
        elif et == FeedbackEventType.PRODUCT_IMPRESSION.value:
            stats = self.repository.interactions.setdefault(key, ProductInteractionStats())
            stats.impression_count += 1
        elif et == FeedbackEventType.PRODUCT_CLICKED.value:
            stats = self.repository.interactions.setdefault(key, ProductInteractionStats())
            stats.click_count += 1
            stats.last_interaction_at = event.occurred_at
            self.repository.bump_revision(event.shopper_id)
        elif et == FeedbackEventType.PRODUCT_DETAIL_VIEWED.value:
            stats = self.repository.interactions.setdefault(key, ProductInteractionStats())
            stats.detail_view_count += 1
            stats.last_interaction_at = event.occurred_at
            self.repository.bump_revision(event.shopper_id)
        elif et == FeedbackEventType.VTO_COMPLETED.value:
            product_id = str(event.context.get("product_id", event.subject_id))
            stats = self.repository.interactions.setdefault(
                (event.shopper_id, product_id), ProductInteractionStats()
            )
            stats.vto_completed_count += 1
        elif et == FeedbackEventType.VTO_FAILED.value:
            # Operational failure only; never mutate product reaction or preference negatively
            product_id = str(event.context.get("product_id", event.subject_id))
            stats = self.repository.interactions.setdefault(
                (event.shopper_id, product_id), ProductInteractionStats()
            )
            stats.vto_failed_count += 1
        elif et == FeedbackEventType.MERCHANT_OUTBOUND_CLICKED.value:
            product_id = str(event.context.get("product_id", event.subject_id))
            stats = self.repository.interactions.setdefault(
                (event.shopper_id, product_id), ProductInteractionStats()
            )
            stats.outbound_click_count += 1
            stats.last_interaction_at = event.occurred_at

    def _set_reaction(
        self,
        shopper_id: str,
        product_id: str,
        reaction: ReactionState,
        source_event_id: UUID,
        now: datetime,
    ) -> None:
        self.repository.reactions[(shopper_id, product_id)] = ProductReactionProjection(
            shopper_id=shopper_id,
            product_id=product_id,
            reaction=reaction,
            source_event_id=source_event_id,
            updated_at=now,
        )
        self.repository.bump_revision(shopper_id)
