from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CanonicalGarment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID | None = None
    display_name: str
    category: str
    subcategory: str | None = None
    version: int = Field(default=1, ge=1)


class MerchantOffer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_id: UUID
    merchant_id: UUID
    source_product_id: str
    url: str
    price_minor: int = Field(ge=0)
    currency: str = "INR"
    in_stock: bool = True
