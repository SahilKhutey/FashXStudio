from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common.enums import GarmentImageType


class GarmentImageCreate(BaseModel):
    storage_key: str = Field(min_length=1, max_length=1024)
    content_hash: str = Field(min_length=32, max_length=128)
    perceptual_hash: str | None = Field(default=None, max_length=255)
    image_type: GarmentImageType


class GarmentImage(BaseModel):
    id: UUID
    garment_id: UUID
    storage_key: str
    content_hash: str
    perceptual_hash: str | None = None
    image_type: GarmentImageType
    version: int = Field(default=1, ge=1)
