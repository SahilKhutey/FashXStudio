from dataclasses import dataclass, field
from uuid import UUID

from database.models.commerce_feedback import TryOnFeedback
from database.models.tryon import TryOnJob
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import AuthorizationError, NotFoundError, ValidationError


@dataclass(frozen=True)
class SubmitTryOnFeedbackCommand:
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: str
    purchase_confidence: int | None = None
    issue_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubmitTryOnFeedbackResult:
    feedback_id: UUID
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: str
    purchase_confidence: int | None
    issue_tags: list[str] = field(default_factory=list)


class SubmitTryOnFeedbackUseCase:
    """Records try-on realism perception and user purchase confidence (Rule I14)."""

    VALID_ACCURACIES = {
        "very_inaccurate",
        "inaccurate",
        "neutral",
        "accurate",
        "very_accurate",
    }

    VALID_ISSUE_TAGS = {
        "unnatural_fit",
        "garment_distorted",
        "color_inaccurate",
        "blurry_artifacts",
        "person_appearance_changed",
        "wrong_garment",
        "occlusion_error",
    }

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: SubmitTryOnFeedbackCommand) -> SubmitTryOnFeedbackResult:
        if cmd.visual_accuracy not in self.VALID_ACCURACIES:
            raise ValidationError(
                f"Invalid visual accuracy '{cmd.visual_accuracy}'; must be one of {sorted(self.VALID_ACCURACIES)}",
                field="visual_accuracy",
            )

        if cmd.purchase_confidence is not None and not (1 <= cmd.purchase_confidence <= 5):
            raise ValidationError(
                f"Purchase confidence must be between 1 and 5; got {cmd.purchase_confidence}",
                field="purchase_confidence",
            )

        for tag in cmd.issue_tags:
            if tag not in self.VALID_ISSUE_TAGS:
                raise ValidationError(
                    f"Invalid issue tag '{tag}'; must be one of {sorted(self.VALID_ISSUE_TAGS)}",
                    field="issue_tags",
                )

        cleaned_issue_tags = sorted(set(cmd.issue_tags))

        async with self.uow:
            job = await self.uow.session.get(TryOnJob, cmd.tryon_job_id)
            if job is None:
                raise NotFoundError(
                    f"Try-on job {cmd.tryon_job_id} not found",
                    field="tryon_job_id",
                )

            if job.user_id != cmd.user_id:
                raise AuthorizationError(
                    f"User {cmd.user_id} cannot submit feedback for try-on job {cmd.tryon_job_id}"
                )

            if job.status != "completed":
                raise ValidationError(
                    f"Cannot submit feedback for job in status '{job.status}'; must be 'completed'",
                    field="tryon_job_id",
                )

            existing = await self.uow.tryon_feedback.get_by_user_and_job(
                cmd.user_id, cmd.tryon_job_id
            )
            if existing is not None:
                return SubmitTryOnFeedbackResult(
                    feedback_id=existing.id,
                    user_id=existing.user_id,
                    tryon_job_id=existing.tryon_job_id,
                    visual_accuracy=existing.visual_accuracy,
                    purchase_confidence=existing.purchase_confidence,
                    issue_tags=list(existing.issue_tags or []),
                )

            provider = getattr(job, "provider", None) or "mock"

            feedback = TryOnFeedback(
                user_id=cmd.user_id,
                tryon_job_id=cmd.tryon_job_id,
                visual_accuracy=cmd.visual_accuracy,
                purchase_confidence=cmd.purchase_confidence,
                provider=provider,
                issue_tags=cleaned_issue_tags,
            )
            self.uow.tryon_feedback.add(feedback)
            await self.uow.commit()

        return SubmitTryOnFeedbackResult(
            feedback_id=feedback.id,
            user_id=feedback.user_id,
            tryon_job_id=feedback.tryon_job_id,
            visual_accuracy=feedback.visual_accuracy,
            purchase_confidence=feedback.purchase_confidence,
            issue_tags=list(feedback.issue_tags or []),
        )
