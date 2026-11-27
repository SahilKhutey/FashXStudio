"""In-memory durable-style repository for Phase 08.5 events, outbox, and projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from fashx.feedback.enums import ReactionState
from fashx.feedback.idempotency import FeedbackConflict


@dataclass
class StoredFeedbackEvent:
    event_id: UUID
    shopper_id: str
    event_type: str
    feedback_class: str
    subject_type: str
    subject_id: str
    occurred_at: datetime
    received_at: datetime
    recorded_at: datetime
    processed_at: datetime | None
    source: str
    session_id: str | None
    context: dict[str, object]
    consent_revision: int
    schema_version: int
    payload_hash: str
    processing_status: str = "PENDING"


@dataclass
class ProcessingLedgerEntry:
    event_id: UUID
    shopper_id: str
    status: str = "PENDING"
    attempts: int = 0
    processed_at: datetime | None = None
    last_error_code: str | None = None


@dataclass
class OutboxEntry:
    event_id: UUID
    shopper_id: str
    status: str = "PENDING"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProductReactionProjection:
    shopper_id: str
    product_id: str
    reaction: ReactionState
    source_event_id: UUID
    updated_at: datetime


@dataclass
class SavedProductProjection:
    shopper_id: str
    product_id: str
    merchant_offer_id: str | None
    is_saved: bool
    source_event_id: UUID
    saved_at: datetime | None
    updated_at: datetime


@dataclass
class ProductInteractionStats:
    click_count: int = 0
    detail_view_count: int = 0
    impression_count: int = 0
    vto_completed_count: int = 0
    vto_failed_count: int = 0
    outbound_click_count: int = 0
    last_interaction_at: datetime | None = None


class InMemoryFeedbackRepository:
    """Atomic event + outbox + processing-ledger + projection store."""

    def __init__(self) -> None:
        self.events: dict[UUID, StoredFeedbackEvent] = {}
        self.processing: dict[UUID, ProcessingLedgerEntry] = {}
        self.outbox: list[OutboxEntry] = []
        self.reactions: dict[tuple[str, str], ProductReactionProjection] = {}
        self.saved: dict[tuple[str, str], SavedProductProjection] = {}
        self.interactions: dict[tuple[str, str], ProductInteractionStats] = {}
        self.vto_quality_feedback: dict[tuple[str, str], dict[str, object]] = {}
        self.preference_revisions: dict[str, int] = {}
        self.vto_job_owners: dict[str, str] = {}
        self.valid_products: set[str] | None = None

    def register_vto_job_owner(self, job_id: str, shopper_id: str) -> None:
        self.vto_job_owners[job_id] = shopper_id

    def get_by_event_id(self, event_id: UUID) -> StoredFeedbackEvent | None:
        return self.events.get(event_id)

    def count_by_event_id(self, event_id: UUID) -> int:
        return 1 if event_id in self.events else 0

    def create_event_and_outbox(
        self,
        *,
        event_id: UUID,
        shopper_id: str,
        event_type: str,
        feedback_class: str,
        subject_type: str,
        subject_id: str,
        occurred_at: datetime,
        received_at: datetime,
        source: str,
        session_id: str | None,
        context: dict[str, object],
        consent_revision: int,
        schema_version: int,
        payload_hash: str,
    ) -> StoredFeedbackEvent:
        existing = self.events.get(event_id)
        if existing is not None:
            if existing.shopper_id != shopper_id or existing.payload_hash != payload_hash:
                raise FeedbackConflict("Event ID reused with different shopper or payload")
            return existing

        now = datetime.now(UTC)
        rec = StoredFeedbackEvent(
            event_id=event_id,
            shopper_id=shopper_id,
            event_type=event_type,
            feedback_class=feedback_class,
            subject_type=subject_type,
            subject_id=subject_id,
            occurred_at=occurred_at,
            received_at=received_at,
            recorded_at=now,
            processed_at=None,
            source=source,
            session_id=session_id,
            context=dict(context),
            consent_revision=consent_revision,
            schema_version=schema_version,
            payload_hash=payload_hash,
            processing_status="PENDING",
        )
        self.events[event_id] = rec
        self.processing[event_id] = ProcessingLedgerEntry(event_id=event_id, shopper_id=shopper_id)
        self.outbox.append(OutboxEntry(event_id=event_id, shopper_id=shopper_id))
        return rec

    def get_reaction(self, shopper_id: str, product_id: str) -> ReactionState:
        proj = self.reactions.get((shopper_id, product_id))
        return proj.reaction if proj else ReactionState.NONE

    def get_saved(self, shopper_id: str, product_id: str) -> SavedProductProjection | None:
        return self.saved.get((shopper_id, product_id))

    def bump_revision(self, shopper_id: str) -> int:
        rev = self.preference_revisions.get(shopper_id, 1) + 1
        self.preference_revisions[shopper_id] = rev
        return rev

    def clear_personalization_projections(self, shopper_id: str) -> None:
        for k in [key for key in self.reactions if key[0] == shopper_id]:
            del self.reactions[k]
        for k in [key for key in self.saved if key[0] == shopper_id]:
            del self.saved[k]
        for k in [key for key in self.interactions if key[0] == shopper_id]:
            del self.interactions[k]
        self.bump_revision(shopper_id)
