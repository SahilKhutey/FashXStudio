from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfilePhotoJobResponse(BaseModel):
    job_id: UUID
    photo_id: UUID
    status: str
    failure_reason: str | None = None
    attempt_count: int = 0
    created_at: datetime


class PhotoJobClaimResponse(BaseModel):
    claimed: bool
    reason: str | None = None
    job_id: UUID | None = None
    photo_id: UUID | None = None
    user_id: UUID | None = None
    photo_type: str | None = None
    storage_key: str | None = None
    attempt_count: int | None = None


class PhotoJobCompleteRequest(BaseModel):
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    image_format: str = Field(min_length=1, max_length=16)
    mode: str = Field(min_length=1, max_length=32)
    has_person: bool | None = None
    has_face: bool | None = None
    file_size_bytes: int = Field(ge=1)


class PhotoJobFailRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=255)
    retryable: bool = False


class PhotoJobFailureResponse(BaseModel):
    status: str
    retry_scheduled: bool
    attempt_count: int
    failure_reason: str | None = None
