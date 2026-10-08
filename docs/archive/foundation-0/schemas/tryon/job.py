from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import TryOnFailureReason, TryOnStatus


class TryOnCreate(BaseModel):
    product_id: UUID


class TryOnJob(BaseModel):
    id: UUID
    user_id: UUID
    garment_id: UUID
    profile_photo_id: UUID
    idempotency_key: str
    artifact_key: str
    status: TryOnStatus
    model_version: str
    pipeline_version: str
    failure_reason: TryOnFailureReason | None = None


class TryOnStatusResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
    result_url: str | None = None
    failure_reason: TryOnFailureReason | None = None
