"""Shopper fit feedback service enforcing snapshot binding, ownership, triage, and deletion (Task 8.3.12)."""

from __future__ import annotations

from uuid import UUID

from database.models.commerce_feedback import FitFeedback
from database.models.tryon import FitRecommendation
from fashx.fit.contracts import (
    FitFeedbackCreateRequest,
    FitFeedbackResponse,
    FitFeedbackReviewRequest,
)
from fashx.fit.enums import FeedbackReviewStatus, FitFeedbackReason
from fashx.fit.repository import FitRecommendationRepository


def _to_feedback_response(fb: FitFeedback, *, rec: FitRecommendation | None = None) -> FitFeedbackResponse:
    rec_id = getattr(fb, "_raw_rec_id", str(fb.recommendation_id))
    prod_id = getattr(fb, "_raw_product_id", str(fb.garment_id))
    merch_id = getattr(
        fb,
        "_raw_merchant_id",
        str(fb.merchant_id) if fb.merchant_id else None,
    )
    chart_id = getattr(
        fb,
        "_raw_chart_id",
        str(fb.size_chart_id) if fb.size_chart_id else None,
    )
    if rec is not None and rec.recommended_size:
        rec_size: str | None = rec.recommended_size
    elif fb.size_label and fb.size_label != "ABSTAINED":
        rec_size = fb.size_label
    else:
        rec_size = None

    return FitFeedbackResponse(
        feedback_id=str(fb.id),
        recommendation_id=rec_id,
        product_id=prod_id,
        merchant_id=merch_id,
        size_chart_id=chart_id,
        size_chart_revision=fb.size_chart_revision,
        recommended_size=rec_size,
        reason=FitFeedbackReason(fb.reason or fb.verdict),
        purchase_status=fb.purchase_status,  # type: ignore[arg-type]
        tried_on=fb.tried_on,
        kept_item=fb.kept_item,
        selected_different_size=fb.selected_different_size,
        feedback_basis=fb.feedback_basis,
        review_status=FeedbackReviewStatus(fb.review_status),
        comment=fb.comment,
        created_at=fb.created_at,
    )


class FitFeedbackService:
    """Manages shopper fit feedback without trusting client product/merchant IDs or auto-mutating rules."""

    def __init__(self, repository: FitRecommendationRepository | None = None) -> None:
        self.repo = repository or FitRecommendationRepository()

    async def submit(
        self,
        *,
        shopper_id: UUID | str,
        recommendation_id: UUID | str,
        payload: FitFeedbackCreateRequest,
        category: str = "UNKNOWN",
    ) -> FitFeedbackResponse:
        rec = await self.repo.get_recommendation_for_owner(recommendation_id, shopper_id)
        feedback_basis = "PHYSICAL_TRYON" if payload.tried_on else "RECOMMENDATION_ONLY"
        initial_review = (
            FeedbackReviewStatus.PENDING_REVIEW.value
            if payload.tried_on
            else FeedbackReviewStatus.UNVERIFIED.value
        )

        fb = await self.repo.save_feedback(
            recommendation=rec,
            shopper_id=shopper_id,
            reason=payload.reason.value,
            purchase_status=payload.purchase_status.value,
            tried_on=payload.tried_on,
            kept_item=payload.kept_item,
            selected_different_size=payload.selected_different_size,
            feedback_basis=feedback_basis,
            review_status=initial_review,
            comment=payload.comment,
            category=category,
        )
        return _to_feedback_response(fb, rec=rec)

    async def get_own_feedback(
        self,
        *,
        shopper_id: UUID | str,
        recommendation_id: UUID | str,
    ) -> FitFeedbackResponse:
        rec = await self.repo.get_recommendation_for_owner(recommendation_id, shopper_id)
        fb = await self.repo.get_feedback_for_recommendation(recommendation_id, shopper_id)
        if fb is None:
            raise KeyError(f"No feedback recorded for recommendation '{recommendation_id}'.")
        return _to_feedback_response(fb, rec=rec)

    async def triage_feedback(
        self,
        *,
        feedback_id: UUID | str,
        review: FitFeedbackReviewRequest,
    ) -> FitFeedbackResponse:
        """Record human review triage decision. Never auto-modifies fit rules."""
        fb = await self.repo.review_feedback(
            feedback_id,
            review_status=review.review_status.value,
        )
        return _to_feedback_response(fb)

    async def delete_feedback(
        self,
        *,
        shopper_id: UUID | str,
        feedback_id: UUID | str,
    ) -> bool:
        return await self.repo.delete_feedback(feedback_id, shopper_id)
