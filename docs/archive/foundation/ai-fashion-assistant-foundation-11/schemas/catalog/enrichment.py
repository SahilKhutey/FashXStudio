from uuid import UUID

from pydantic import BaseModel, Field


class ConfidenceValue(BaseModel):
    value: str | list[str] | None
    confidence: float = Field(ge=0, le=1)


class GarmentEnrichment(BaseModel):
    garment_id: UUID
    model_version: str
    silhouette: ConfidenceValue | None = None
    neckline: ConfidenceValue | None = None
    sleeve_length: ConfidenceValue | None = None
    pattern: ConfidenceValue | None = None
    colors: ConfidenceValue | None = None
    occasion: ConfidenceValue | None = None
    formality: ConfidenceValue | None = None
