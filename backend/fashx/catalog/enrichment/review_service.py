from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from fashx.catalog.taxonomy.registry import TaxonomyRegistry


class ReviewAction(StrEnum):
    APPROVE = "APPROVE"
    CORRECT = "CORRECT"
    REJECT = "REJECT"
    MARK_UNKNOWN = "MARK_UNKNOWN"


class ReviewStatusState(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"


class ReviewPermissionError(PermissionError):
    """Raised when an unauthorized actor attempts cross-merchant or restricted review actions."""


@dataclass
class ReviewRecord:
    id: UUID
    product_id: str
    merchant_id: str
    attribute_id: str
    proposed_value: Any
    current_value: Any
    status: ReviewStatusState
    confidence: float | None
    flags: list[str] = field(default_factory=list)
    reason: str | None = None
    assigned_to: str | None = None
    reviewed_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None


@dataclass
class ReviewEvent:
    id: UUID
    review_id: UUID
    actor_id: str
    action: ReviewAction
    previous_value: Any
    new_value: Any
    reason: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryReviewRepository:
    """Repository storing review tasks and append-only audit events."""

    def __init__(self) -> None:
        self.reviews: dict[UUID, ReviewRecord] = {}
        self.events: list[ReviewEvent] = []

    def save_review(self, record: ReviewRecord) -> None:
        self.reviews[record.id] = record

    def get_review(self, review_id: UUID) -> ReviewRecord | None:
        return self.reviews.get(review_id)

    def list_pending_reviews(self, merchant_id: str | None = None) -> list[ReviewRecord]:
        items = [
            r for r in self.reviews.values() if r.status == ReviewStatusState.PENDING
        ]
        if merchant_id is not None:
            items = [r for r in items if r.merchant_id == merchant_id]
        return items

    def record_event(self, event: ReviewEvent) -> None:
        self.events.append(event)

    def list_events(self, review_id: UUID) -> list[ReviewEvent]:
        return [e for e in self.events if e.review_id == review_id]


class ReviewService:
    """Manages the human review lifecycle with tenant isolation and audit preservation."""

    def __init__(self, repo: InMemoryReviewRepository | None = None) -> None:
        self.repo = repo or InMemoryReviewRepository()

    def create_review_task(
        self,
        product_id: str,
        merchant_id: str,
        attribute_id: str,
        proposed_value: Any,
        current_value: Any,
        confidence: float | None,
        flags: list[str],
        reason: str | None = None,
    ) -> ReviewRecord:
        review = ReviewRecord(
            id=uuid4(),
            product_id=product_id,
            merchant_id=merchant_id,
            attribute_id=attribute_id,
            proposed_value=proposed_value,
            current_value=current_value,
            status=ReviewStatusState.PENDING,
            confidence=confidence,
            flags=flags,
            reason=reason,
        )
        self.repo.save_review(review)
        return review

    def _verify_access(
        self,
        review: ReviewRecord,
        actor_role: str,
        actor_merchant_id: str | None,
    ) -> None:
        """Enforce Rule 6.2.14 / ENR-031: Merchant reviewer can only access their own products."""
        if actor_role in {"PLATFORM_ADMIN", "PLATFORM_REVIEWER"}:
            return
        if actor_role == "MERCHANT_REVIEWER":
            if actor_merchant_id != review.merchant_id:
                raise ReviewPermissionError(
                    f"Access denied: Merchant '{actor_merchant_id}' cannot review product belonging to '{review.merchant_id}'"
                )
            return
        raise ReviewPermissionError(f"Unauthorized role: {actor_role}")

    def approve_attribute(
        self,
        review_id: UUID,
        actor_id: str,
        actor_role: str,
        actor_merchant_id: str | None = None,
        reason: str | None = "Approved by human reviewer",
    ) -> ReviewRecord:
        review = self.repo.get_review(review_id)
        if review is None:
            raise ValueError(f"Review record {review_id} not found")
        self._verify_access(review, actor_role, actor_merchant_id)

        now = datetime.now(UTC)
        prev_val = review.current_value
        review.status = ReviewStatusState.APPROVED
        review.current_value = review.proposed_value
        review.reviewed_by = actor_id
        review.reviewed_at = now

        self.repo.record_event(
            ReviewEvent(
                id=uuid4(),
                review_id=review.id,
                actor_id=actor_id,
                action=ReviewAction.APPROVE,
                previous_value=prev_val,
                new_value=review.current_value,
                reason=reason,
                created_at=now,
            )
        )
        self.repo.save_review(review)
        return review

    def correct_attribute(
        self,
        review_id: UUID,
        corrected_value: str,
        registry: TaxonomyRegistry,
        actor_id: str,
        actor_role: str,
        actor_merchant_id: str | None = None,
        reason: str = "Corrected to valid taxonomy value",
    ) -> ReviewRecord:
        review = self.repo.get_review(review_id)
        if review is None:
            raise ValueError(f"Review record {review_id} not found")
        self._verify_access(review, actor_role, actor_merchant_id)

        # Validate that the corrected value conforms to the taxonomy dictionary
        attr_id = review.attribute_id
        if attr_id == "color" and not registry.is_valid_color(corrected_value):
            raise ValueError(f"Corrected color '{corrected_value}' is not a valid taxonomy color")
        if attr_id == "pattern" and not registry.is_valid_pattern(corrected_value):
            raise ValueError(f"Corrected pattern '{corrected_value}' is not a valid taxonomy pattern")

        now = datetime.now(UTC)
        prev_val = review.current_value
        review.status = ReviewStatusState.CORRECTED
        review.current_value = corrected_value
        review.reviewed_by = actor_id
        review.reviewed_at = now

        self.repo.record_event(
            ReviewEvent(
                id=uuid4(),
                review_id=review.id,
                actor_id=actor_id,
                action=ReviewAction.CORRECT,
                previous_value=prev_val,
                new_value=corrected_value,
                reason=reason,
                created_at=now,
            )
        )
        self.repo.save_review(review)
        return review

    def reject_attribute(
        self,
        review_id: UUID,
        actor_id: str,
        actor_role: str,
        actor_merchant_id: str | None = None,
        reason: str = "Rejected by reviewer",
    ) -> ReviewRecord:
        review = self.repo.get_review(review_id)
        if review is None:
            raise ValueError(f"Review record {review_id} not found")
        self._verify_access(review, actor_role, actor_merchant_id)

        now = datetime.now(UTC)
        prev_val = review.current_value
        review.status = ReviewStatusState.REJECTED
        review.reviewed_by = actor_id
        review.reviewed_at = now

        self.repo.record_event(
            ReviewEvent(
                id=uuid4(),
                review_id=review.id,
                actor_id=actor_id,
                action=ReviewAction.REJECT,
                previous_value=prev_val,
                new_value=None,
                reason=reason,
                created_at=now,
            )
        )
        self.repo.save_review(review)
        return review
