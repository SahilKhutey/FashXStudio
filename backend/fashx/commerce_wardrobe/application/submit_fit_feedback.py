from dataclasses import dataclass
from uuid import UUID

from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import ValidationError
from database.models.commerce_feedback import FitFeedback


@dataclass(frozen=True)
class SubmitFitFeedbackCommand:
    user_id: UUID
    garment_id: UUID
    brand_id: UUID
    category: str
    size_label: str
    verdict: str  # 'too_tight', 'true_to_size', 'too_loose'
    fit_type: str | None = None
    buy_click_id: UUID | None = None


@dataclass(frozen=True)
class SubmitFitFeedbackResult:
    feedback_id: UUID
    user_id: UUID
    brand_id: UUID
    verdict: str
    brand_bias_score: float
    brand_recommendation: str
    total_observations: int


class SubmitFitFeedbackUseCase:
    """Records granular purchase fit feedback and computes real-time sizing bias (Rule I13)."""

    VALID_VERDICTS = {"too_tight", "true_to_size", "too_loose"}

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: SubmitFitFeedbackCommand) -> SubmitFitFeedbackResult:
        if cmd.verdict not in self.VALID_VERDICTS:
            raise ValidationError(
                f"Invalid fit verdict '{cmd.verdict}'; must be one of {self.VALID_VERDICTS}",
                field="verdict",
            )

        async with self.uow:
            feedback = FitFeedback(
                user_id=cmd.user_id,
                garment_id=cmd.garment_id,
                brand_id=cmd.brand_id,
                category=cmd.category,
                fit_type=cmd.fit_type,
                size_label=cmd.size_label,
                verdict=cmd.verdict,
                buy_click_id=cmd.buy_click_id,
            )
            self.uow.fit_feedback.add(feedback)
            await self.uow.commit()
            feedback_id = feedback.id

            # Re-compute brand sizing bias metrics
            metrics = await self.uow.fit_feedback.compute_brand_bias(
                brand_id=cmd.brand_id, category=cmd.category
            )

        return SubmitFitFeedbackResult(
            feedback_id=feedback_id,
            user_id=cmd.user_id,
            brand_id=cmd.brand_id,
            verdict=cmd.verdict,
            brand_bias_score=float(metrics["bias_score"]),
            brand_recommendation=str(metrics["recommendation"]),
            total_observations=int(metrics["total_observations"]),
        )
