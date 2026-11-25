from __future__ import annotations

import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fashx.tryon.feedback.schemas import (
    FeedbackReviewStatus,
    FeedbackSeverity,
    TryOnFeedbackRequest,
    TryOnFeedbackResponse,
    TryOnFeedbackReviewAction,
)


class FeedbackSecurityError(PermissionError):
    """Raised when a user attempts to report or access another shopper's try-on job."""

    pass


class FeedbackRateLimitExceeded(ValueError):
    """Raised when feedback submission velocity exceeds safe rate limits."""

    pass


class FeedbackInvalidJobState(ValueError):
    """Raised when feedback is submitted for a job with no generated output."""

    pass


class TryOnFeedbackService:
    """Service managing shopper try-on feedback, privacy gates, reviewer triage, and evaluation linkage."""

    RATE_LIMIT_WINDOW_SECONDS = 600
    RATE_LIMIT_MAX_SUBMISSIONS = 5

    def __init__(self, session_or_db: Any = None) -> None:
        self.session = session_or_db
        # Ephemeral sliding-window tracking for rate limits and fast testing
        self._user_timestamps: dict[str, list[float]] = defaultdict(list)
        # Ephemeral in-memory store for fallback/tests
        self._feedback_records: dict[str, dict[str, Any]] = {}
        self._job_feedback_index: dict[tuple[str, str], str] = {}
        self._review_records: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def _check_rate_limit(self, user_id: str) -> None:
        now = time.time()
        window_start = now - self.RATE_LIMIT_WINDOW_SECONDS
        recent = [t for t in self._user_timestamps[user_id] if t >= window_start]
        if len(recent) >= self.RATE_LIMIT_MAX_SUBMISSIONS:
            raise FeedbackRateLimitExceeded(
                f"Rate limit exceeded: maximum {self.RATE_LIMIT_MAX_SUBMISSIONS} feedback reports per 10 minutes."
            )
        recent.append(now)
        self._user_timestamps[user_id] = recent

    async def submit_feedback(
        self,
        *,
        authenticated_user_id: str | UUID,
        job_id: str | UUID,
        request: TryOnFeedbackRequest,
        job_owner_id: str | UUID | None = None,
        job_status: str = "completed",
        has_result: bool = True,
        provider: str | None = None,
        model_version: str | None = None,
    ) -> TryOnFeedbackResponse:
        user_str = str(authenticated_user_id)
        job_str = str(job_id)

        # 1. Rate limiting
        self._check_rate_limit(user_str)

        # 2. Authorization & Ownership verification
        if job_owner_id is not None and str(job_owner_id) != user_str:
            raise FeedbackSecurityError(f"User '{user_str}' is not authorized to submit feedback for job '{job_str}'.")

        # 3. Status verification (must have completed a result)
        if job_status.lower() != "completed" or not has_result:
            raise FeedbackInvalidJobState(
                f"Cannot submit feedback for job in status '{job_status}'. Only completed results can be reported."
            )

        # 4. Idempotency: return existing report if already submitted for same (user, job)
        cache_key = (user_str, job_str)
        if cache_key in self._job_feedback_index:
            existing_id = self._job_feedback_index[cache_key]
            rec = self._feedback_records[existing_id]
            return TryOnFeedbackResponse(
                feedback_id=rec["feedback_id"],
                job_id=rec["job_id"],
                user_id=rec["user_id"],
                reason_code=rec["reason_code"],
                status=rec["status"],
                include_in_quality_review=rec["include_in_quality_review"],
                message="Feedback already recorded for this try-on result.",
                created_at=rec["created_at"],
            )

        # 5. Record creation
        feedback_id = f"fdbk_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        record = {
            "feedback_id": feedback_id,
            "job_id": job_str,
            "user_id": user_str,
            "reason_code": request.reason_code,
            "details": request.details,
            "include_in_quality_review": request.include_in_quality_review,
            "status": FeedbackReviewStatus.RECEIVED,
            "provider": provider or "fashn",
            "model_version": model_version or "v1.5",
            "created_at": now,
            "updated_at": now,
        }
        self._feedback_records[feedback_id] = record
        self._job_feedback_index[cache_key] = feedback_id

        # Crucial invariant: original VTO job is NOT mutated or deleted
        return TryOnFeedbackResponse(
            feedback_id=feedback_id,
            job_id=job_str,
            user_id=user_str,
            reason_code=request.reason_code,
            status=FeedbackReviewStatus.RECEIVED,
            include_in_quality_review=request.include_in_quality_review,
            message="Your feedback has been recorded.",
            created_at=now,
        )

    async def get_feedback(
        self,
        *,
        authenticated_user_id: str | UUID,
        feedback_id: str,
    ) -> TryOnFeedbackResponse:
        user_str = str(authenticated_user_id)
        if feedback_id not in self._feedback_records:
            raise KeyError(f"Feedback '{feedback_id}' not found.")
        rec = self._feedback_records[feedback_id]
        if rec["user_id"] != user_str:
            raise FeedbackSecurityError(f"User '{user_str}' cannot access feedback '{feedback_id}'.")

        return TryOnFeedbackResponse(
            feedback_id=rec["feedback_id"],
            job_id=rec["job_id"],
            user_id=rec["user_id"],
            reason_code=rec["reason_code"],
            status=rec["status"],
            include_in_quality_review=rec["include_in_quality_review"],
            message="Feedback retrieved.",
            created_at=rec["created_at"],
        )

    async def review_feedback(
        self,
        *,
        feedback_id: str,
        action: TryOnFeedbackReviewAction,
    ) -> dict[str, Any]:
        """Triage, investigation, and evaluation dataset linkage performed by authorized reviewers."""
        if feedback_id not in self._feedback_records:
            raise KeyError(f"Feedback '{feedback_id}' not found.")

        rec = self._feedback_records[feedback_id]
        rec["status"] = action.review_status
        rec["updated_at"] = datetime.now(UTC)

        review_entry = {
            "review_id": f"rev_{uuid.uuid4().hex[:12]}",
            "feedback_id": feedback_id,
            "reviewer_id": action.reviewer_id,
            "status": action.review_status,
            "root_cause": action.root_cause,
            "severity": action.severity,
            "resolution_notes": action.resolution_notes,
            "linked_evaluation_item_id": action.linked_evaluation_item_id,
            "reviewed_at": datetime.now(UTC),
        }
        self._review_records[feedback_id].append(review_entry)

        # Escalation policy: Critical issues trigger category safety review
        category_escalated = False
        if action.severity == FeedbackSeverity.CRITICAL or action.review_status == FeedbackReviewStatus.ESCALATED:
            category_escalated = True

        # Linkage to Phase 07.7: If confirmed and shopper permitted quality review, create evaluation item
        evaluation_candidate_created = False
        if (
            action.review_status == FeedbackReviewStatus.CONFIRMED
            and rec["include_in_quality_review"]
        ):
            evaluation_candidate_created = True

        return {
            "feedback_id": feedback_id,
            "status": action.review_status,
            "reviewer_id": action.reviewer_id,
            "category_escalated": category_escalated,
            "evaluation_candidate_created": evaluation_candidate_created,
            "quality_review_permitted": rec["include_in_quality_review"],
        }
