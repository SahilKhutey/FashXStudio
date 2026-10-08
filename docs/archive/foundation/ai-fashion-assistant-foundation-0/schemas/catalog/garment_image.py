from uuid import UUID

from pydantic import BaseModel

from schemas.common.enums import GarmentImageType


class GarmentImage(BaseModel):
    id: UUID
    garment_id: UUID
    storage_key: str
    content_hash: str
    perceptual_hash: str | None = None
    image_type: GarmentImageType
