from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from schemas.catalog.enrichment import GarmentEnrichment
from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.catalog.garment_image import GarmentImage


class CatalogImageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_type: str
    url: str | None = None
    version: int = Field(default=1, ge=1)


class CatalogOfferView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    source_product_id: str
    url: str
    price_minor: int = Field(ge=0)
    currency: str = "INR"
    in_stock: bool = True
    selected: bool = False


class CatalogDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    garment: CanonicalGarment
    images: list[CatalogImageView]
    offers: list[CatalogOfferView]
    enrichment: GarmentEnrichment | None = None
    selected_offer_id: str | None = None


class CatalogOfferSelection(BaseModel):
    offer_id: str


class SaveCatalogItemRequest(BaseModel):
    offer_id: str | None = None
    snapshot_image_id: str | None = None


class SaveCatalogItemResponse(BaseModel):
    wardrobe_item_id: str
    garment_id: str
    offer_id: str | None = None
    already_saved: bool = False


class RejectCatalogItemResponse(BaseModel):
    garment_id: str
    rejected: bool = True
