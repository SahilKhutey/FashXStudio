from datetime import datetime
from pydantic import Field, HttpUrl
from schemas.base import BaseContractModel


class GarmentVariantV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    variant_id: str
    canonical_id: str
    standard_size: str
    normalized_color: str
    color_hex: str = Field(pattern="^#[0-9A-Fa-f]{6}$")
    created_at: datetime


class MerchantOfferV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    offer_id: str
    merchant_product_id: str
    variant_id: str
    price: float = Field(gt=0.0)
    mrp: float = Field(gt=0.0)
    currency: str = "INR"
    in_stock: bool
    affiliate_url: HttpUrl
    attribution_tracking_code: str
    last_verified_at: datetime
