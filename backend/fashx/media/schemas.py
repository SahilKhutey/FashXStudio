from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

UploadPurpose = Literal["PROFILE_PHOTO", "VTO_PERSONAL_PHOTO"]
UploadStatus = Literal[
    "PENDING_UPLOAD",
    "VALIDATING",
    "AVAILABLE",
    "REJECTED",
    "FAILED",
    "EXPIRED",
    "CANCELLED",
]
MediaStatus = Literal["AVAILABLE", "DELETION_PENDING", "DELETED", "QUARANTINED"]


class UploadInitiateRequest(BaseModel):
    purpose: UploadPurpose = Field(
        ...,
        description="Declared purpose for the personal media asset",
        examples=["VTO_PERSONAL_PHOTO"],
    )
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original client filename (metadata only, not used for storage key)",
        examples=["personal-photo.jpg"],
    )
    content_type: str = Field(
        ...,
        description="Declared MIME content type",
        examples=["image/jpeg"],
    )
    declared_size_bytes: int = Field(
        ...,
        ge=10 * 1024,
        le=10 * 1024 * 1024,
        description="Declared file size in bytes (10KB to 10MB)",
        examples=[2457600],
    )
    client_checksum_sha256: str | None = Field(
        default=None,
        description="Optional client-computed SHA-256 checksum",
    )


class UploadInitiateResponse(BaseModel):
    upload_id: UUID
    image_id: UUID
    upload_url: str
    method: Literal["PUT"] = "PUT"
    required_headers: dict[str, str]
    expires_in_seconds: int = 300
    status: Literal["PENDING_UPLOAD"] = "PENDING_UPLOAD"


class UploadCompleteRequest(BaseModel):
    client_checksum_sha256: str | None = Field(
        default=None,
        description="Optional client SHA-256 checksum confirmation",
    )


class UploadStatusResponse(BaseModel):
    upload_id: UUID
    image_id: UUID
    status: UploadStatus
    message: str | None = None


class MediaMetadataResponse(BaseModel):
    id: UUID
    user_id: UUID
    purpose: str
    status: MediaStatus
    content_type: str
    size_bytes: int
    width: int
    height: int
    sha256_normalized: str
    created_at: datetime


class MediaAccessUrlResponse(BaseModel):
    image_id: UUID
    url: str
    expires_in_seconds: int = 60


class MediaDeletionResponse(BaseModel):
    image_id: UUID
    status: Literal["DELETION_PENDING"] = "DELETION_PENDING"
