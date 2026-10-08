from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PriceCreateRequest(BaseModel):
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    amount: Decimal = Field(ge=0)
    currency: str = "INR"
    price_type: str = "base"
    status: str = "active"
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class RuleCreateRequest(BaseModel):
    name: str
    discount_type: str
    discount_value: Decimal = Field(ge=0)
    priority: int = Field(
        default=100,
        ge=0,
    )
    status: str = "active"
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    customer_id: UUID | None = None
    region: str | None = None
    minimum_quantity: int | None = Field(
        default=None,
        ge=1,
    )
    minimum_cart_value: Decimal | None = Field(
        default=None,
        ge=0,
    )
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class PriceCalculateRequest(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    customer_id: UUID | None = None
    region: str | None = None
    currency: str = "INR"
    quantity: int = Field(
        default=1,
        ge=1,
    )
    cart_value: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )


class PriceAdjustmentResponse(BaseModel):
    rule_id: UUID | None
    description: str
    amount: Decimal


class PriceCalculationResponse(BaseModel):
    original_amount: Decimal
    adjustments: list[PriceAdjustmentResponse]
    final_amount: Decimal
    currency: str
