from dataclasses import dataclass
from uuid import UUID

from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import ValidationError
from database.models.commerce_feedback import TryOnFeedback


@dataclass(frozen=True)
class SubmitTryOnFeedbackCommand:
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: str
    purchase_confidence: int | None = None


@dataclass(frozen=True)
class SubmitTryOnFeedbackResult:
    feedback_id: UUID
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: str
    purchase_confidence: int | None


class SubmitTryOnFeedbackUseCase:
    """Records try-on realism perception and user purchase confidence (Rule I14)."""

    VALID_ACCURACIES = {
        "very_inaccurate",
        "inaccurate",
        "neutral",
        "accurate",
        "very_accurate",
    }

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: SubmitTryOnFeedbackCommand) -> SubmitTryOnFeedbackResult:
        if cmd.visual_accuracy not in self.VALID_ACCURACIES:
            raise ValidationError(
                f"Invalid visual accuracy '{cmd.visual_accuracy}'; must be one of {self.VALID_ACCURACIES}",
                field="visual_accuracy",
            )

        if cmd.purchase_confidence is not None and not (1 <= cmd.purchase_confidence <= 5):
            raise ValidationError(
                f"Purchase confidence must be between 1 and 5; got {cmd.purchase_confidence}",
                field="purchase_confidence",
            )

        async with self.uow:
            feedback = TryOnFeedback(
                user_id=cmd.user_id,
                tryon_job_id=cmd.tryon_job_id,
                visual_accuracy=cmd.visual_accuracy,
                purchase_confidence=cmd.purchase_confidence,
            )
            self.uow.tryon_feedback.add(feedback)
            await self.uow.commit()

        return SubmitTryOnFeedbackResult(
            feedback_id=feedback.id,
            user_id=feedback.user_id,
            tryon_job_id=feedback.tryon_job_id,
            visual_accuracy=feedback.visual_accuracy,
            purchase_confidence=feedback.purchase_confidence,
        )
