from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common.enums import TryOnFailureReason, TryOnStatus
from schemas.tryon.result import TryOnResultMetadata


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
    photo_version: int
    garment_version: int
    attempt_count: int = 0
    result: TryOnResultMetadata | None = None
    failure_reason: TryOnFailureReason | None = None
    provider_job_id: str | None = None


class TryOnStatusResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
    result_url: str | None = None
    failure_reason: TryOnFailureReason | None = None
    model_version: str
    pipeline_version: str
    attempt_count: int
    result: TryOnResultMetadata | None = None


class TryOnCreateResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
    cache_hit: bool
    result_url: str | None = None


class TryOnCancelResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
