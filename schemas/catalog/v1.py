"""
Catalog, Garments, Offers and Variants Domain Contracts v1
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field, HttpUrl
from schemas.base import BaseContractModel


class GarmentCategory(str, Enum):
    TOPWEAR = "topwear"
    BOTTOMWEAR = "bottomwear"
    OUTERWEAR = "outerwear"
    FOOTWEAR = "footwear"
    ACCESSORIES = "accessories"


class GarmentSilhouette(str, Enum):
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    BOXY = "boxy"
    STRAIGHT = "straight"
    A_LINE = "a_line"


class RawMerchantVariantV1(BaseContractModel):
    merchant_sku: str
    raw_size: str
    raw_color: str
    price: float = Field(gt=0.0)
    mrp: float = Field(gt=0.0)
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    in_stock: bool
    stock_count: Optional[int] = None


class MerchantProductV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    merchant_product_id: str
    merchant_id: str = Field(description="e.g. 'myntra', 'amazon_in', 'snitch'")
    merchant_sku: str
    source_url: HttpUrl
    raw_title: str
    raw_brand: str
    raw_description: Optional[str] = None
    raw_size_chart: Optional[Dict[str, Any]] = None
    source_image_urls: List[HttpUrl] = Field(min_length=1)
    variants: List[RawMerchantVariantV1] = Field(min_length=1)
    ingested_at: datetime


class CanonicalGarmentV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    canonical_id: str
    category: GarmentCategory
    subcategory: str = Field(description="e.g. 'overshirt', 'chinos', 'hoodie'")
    gender_target: str = Field(pattern="^(men|women|unisex)$")
    silhouette: GarmentSilhouette
    neckline: Optional[str] = None
    sleeves: Optional[str] = None
    pattern: str = "solid"
    primary_color: str
    color_hex: str = Field(pattern="^#[0-9A-Fa-f]{6}$")
    color_palette_type: str
    material: str
    fabric_weight_gsm: Optional[int] = Field(default=None, gt=0, lt=1000)
    occasion_tags: List[str] = Field(default_factory=list)
    formality_level: str = "casual"
    canonical_images: List[str] = Field(min_length=1)
    flat_lay_image_url: Optional[str] = None
    embedding_siglip: Optional[List[float]] = Field(
        default=None,
        min_length=768,
        max_length=768,
        description="768-dimensional multimodal SigLIP vector",
    )
    enrichment_confidence: float = Field(ge=0.0, le=1.0)
    garment_version: int = Field(default=1, ge=1)
    created_at: datetime


class GarmentVariantV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    variant_id: str
    canonical_id: str
    standard_size: str = Field(description="Normalized: S, M, L, XL, 30, 32, 34")
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
