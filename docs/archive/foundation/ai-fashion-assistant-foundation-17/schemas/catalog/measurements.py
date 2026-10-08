from uuid import UUID

from pydantic import BaseModel, Field


class SizeMeasurement(BaseModel):
    id: UUID
    garment_id: UUID
    size_label: str
    chest_cm: float | None = Field(default=None, gt=0)
    length_cm: float | None = Field(default=None, gt=0)
    waist_cm: float | None = Field(default=None, gt=0)
    shoulder_cm: float | None = Field(default=None, gt=0)
    source: str
    needs_review: bool = False
