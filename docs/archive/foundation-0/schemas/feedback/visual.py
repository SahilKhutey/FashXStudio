from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import VisualAccuracy


class TryOnFeedbackCreate(BaseModel):
    tryon_job_id: UUID
    visual_accuracy: VisualAccuracy
    purchase_confidence: int | None = None
