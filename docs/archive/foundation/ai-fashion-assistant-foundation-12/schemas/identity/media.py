from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.common.enums import PhotoStatus, PhotoType
from schemas.profile.capture_guidance import CaptureGuidanceResponse


class PhotoCreateRequest(BaseModel):
    photo_type: PhotoType
    content_type: str = Field(pattern=r"^image/(jpeg|png|webp)$")
    file_size_bytes: int = Field(gt=0, le=15 * 1024 * 1024)


class PhotoCreateResponse(BaseModel):
    photo_id: UUID
    status: PhotoStatus
    upload_url: str
    expires_at: datetime


class PhotoCompleteResponse(BaseModel):
    photo_id: UUID
    status: PhotoStatus
    processing_job_id: UUID


class PhotoStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    photo_id: UUID
    photo_type: PhotoType
    status: PhotoStatus
    reject_reason: str | None = None
    version: int
    created_at: datetime
    quality_score: float | None = None
    pose_score: float | None = None
    framing_score: float | None = None
    landmark_confidence: float | None = None
    ready_for_tryon: bool | None = None
    quality_reasons: list[str] = Field(default_factory=list)
    pose_provider: str | None = None
    pose_provider_version: str | None = None


class MediaAccessRequest(BaseModel):
    photo_id: UUID
    purpose: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    job_id: UUID


class MediaAccessResponse(BaseModel):
    photo_id: UUID
    access_url: str
    expires_at: datetime
    purpose: str
    job_id: UUID


class PhotoGuidanceResponse(CaptureGuidanceResponse):
    pass
