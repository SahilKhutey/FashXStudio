from uuid import UUID

from pydantic import BaseModel, Field


class WardrobeItem(BaseModel):
    id: UUID
    user_id: UUID
    garment_id: UUID
    offer_id: UUID | None = None
    snapshot_title: str
    snapshot_price_minor: int = Field(ge=0)
    snapshot_currency: str = "INR"
    snapshot_image_key: str
    tryon_artifact_id: UUID | None = None
