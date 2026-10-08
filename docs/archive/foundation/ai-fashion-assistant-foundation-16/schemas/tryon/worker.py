from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common.enums import TryOnFailureReason, TryOnStatus


class TryOnWorkerClaim(BaseModel):
    job_id: UUID
    user_id: UUID
    profile_photo_id: UUID
    garment_id: UUID
    status: str
    model_version: str
    pipeline_version: str
    artifact_key: str
    photo_version: int
    garment_version: int


class TryOnWorkerProgress(BaseModel):
    status: TryOnStatus


class TryOnWorkerFailure(BaseModel):
    reason: TryOnFailureReason
    retryable: bool = False


class TryOnWorkerResultQuality(BaseModel):
    quality_status: str
    quality_score: float
    width: int
    height: int
    size_bytes: int
    content_type: str
    content_sha256: str
    quality_reasons: list[str] = Field(default_factory=list)


class TryOnWorkerComplete(BaseModel):
    result_key: str = Field(min_length=1)
    quality: TryOnWorkerResultQuality


class TryOnWorkerClaimResponse(TryOnWorkerClaim):
    pass
