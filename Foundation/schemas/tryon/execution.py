from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class TryOnExecutionInput(BaseModel):
    job_id: UUID
    user_id: UUID
    photo_key: str
    garment_image_key: str
    model_version: str
    pipeline_version: str
    artifact_key: str
    photo_version: int
    garment_version: int


class TryOnProviderJobResponse(BaseModel):
    provider_job_id: str
