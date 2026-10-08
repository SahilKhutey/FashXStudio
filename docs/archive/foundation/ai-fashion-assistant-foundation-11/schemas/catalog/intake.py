from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

from schemas.catalog.garment_image import GarmentImageCreate


class CatalogIntakeRequest(BaseModel):
    merchant_id: UUID
    brand_id: UUID | None = None
    source_product_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    source_url: AnyHttpUrl
    category: str = Field(min_length=1, max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    price_minor: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    images: list[GarmentImageCreate] = Field(default_factory=list, max_length=12)


class CatalogIntakeResponse(BaseModel):
    product_id: UUID
    merchant_product_id: UUID
    operation: str
    enrichment_required: bool
    ocr_required: bool
    image_count: int
