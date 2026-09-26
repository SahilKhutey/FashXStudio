from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.promotions.enums import (
    DiscountType,
    OfferStatus,
    PromotionScope,
    PromotionStatus,
)


class PromotionCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    code: str | None = Field(
        default=None,
        max_length=100,
    )
    scope: PromotionScope
    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0)
    maximum_discount: Decimal | None = Field(
        default=None,
        ge=0,
    )
    minimum_purchase_value: Decimal | None = Field(
        default=None,
        ge=0,
    )
    start_at: datetime | None = None
    end_at: datetime | None = None
    usage_limit: int | None = Field(
        default=None,
        ge=1,
    )
    per_customer_limit: int | None = Field(
        default=None,
        ge=1,
    )
    metadata: dict[str, str] = Field(default_factory=dict)


class PromotionStatusRequest(BaseModel):
    status: PromotionStatus


class PromotionResponse(BaseModel):
    id: UUID
    name: str
    code: str | None
    status: PromotionStatus
    scope: PromotionScope
    discount_type: DiscountType
    discount_value: Decimal
    maximum_discount: Decimal | None
    minimum_purchase_value: Decimal | None
    start_at: datetime | None
    end_at: datetime | None
    version: int


class OfferCreateRequest(BaseModel):
    promotion_id: UUID
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class OfferStatusRequest(BaseModel):
    status: OfferStatus


class OfferResponse(BaseModel):
    id: UUID
    promotion_id: UUID
    product_id: UUID | None
    variant_id: UUID | None
    listing_id: UUID | None
    status: OfferStatus
    version: int


class CalculateOfferRequest(BaseModel):
    amount: Decimal = Field(ge=0)
    currency: str
    purchase_value: Decimal | None = Field(
        default=None,
        ge=0,
    )


class OfferCalculationResponse(BaseModel):
    base_price_amount: Decimal
    base_price_currency: str
    discount_amount: Decimal
    discount_currency: str
    final_price_amount: Decimal
    final_price_currency: str
    promotion_id: UUID
    offer_id: UUID
