from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common.enums import VisualAccuracy


class TryOnFeedbackCreate(BaseModel):
    tryon_job_id: UUID
    visual_accuracy: VisualAccuracy
    purchase_confidence: int | None = Field(default=None, ge=1, le=5)


class TryOnFeedbackResponse(BaseModel):
    feedback_id: UUID
    tryon_job_id: UUID
    visual_accuracy: VisualAccuracy
    purchase_confidence: int | None
    created_at: str
