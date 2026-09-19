from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import PhotoStatus, PhotoType


class PhotoCreateResponse(BaseModel):
    photo_id: UUID
    status: PhotoStatus
    upload_url: str | None = None
    expires_at: str | None = None


class PhotoStatusResponse(BaseModel):
    photo_id: UUID
    photo_type: PhotoType
    status: PhotoStatus
    reject_reason: str | None = None
