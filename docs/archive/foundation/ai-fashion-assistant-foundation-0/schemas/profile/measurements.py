from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common.enums import MeasurementSource


class UserMeasurement(BaseModel):
    id: UUID
    user_id: UUID
    measurement: str
    value: float = Field(gt=0)
    unit: str
    source: MeasurementSource
    confidence: float | None = Field(default=None, ge=0, le=1)
