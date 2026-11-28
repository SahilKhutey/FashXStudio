from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProductAvailability(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"
    UNKNOWN = "unknown"
    STALE = "stale"
    DELISTED = "delisted"
    TAKEN_DOWN = "taken_down"


class AttributeSource(str, Enum):
    MERCHANT = "merchant"
    SOURCE_FEED = "source_feed"
    AI_ENRICHED = "ai_enriched"
    PLATFORM_VERIFIED = "platform_verified"


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    url: str
    alt_text: str
    position: int = Field(ge=0)
    is_primary: bool = False


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    size_label: str
    color_label: str | None = None
    availability: ProductAvailability


class ProductAttributeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    value: str
    source: AttributeSource
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ProductPermissionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_allowed: bool
    vto_allowed: bool
    redirect_allowed: bool


class MerchantRedirectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redirect_url: str
    expires_at: datetime | None = None
