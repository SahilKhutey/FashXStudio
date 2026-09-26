from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.cart.enums import (
    CartOwnerType,
    CartStatus,
)


class CartCreateRequest(BaseModel):
    owner_type: CartOwnerType = CartOwnerType.ANONYMOUS
    customer_id: UUID | None = None
    session_id: str | None = Field(
        default=None,
        max_length=200,
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )


class CartResponse(BaseModel):
    id: UUID
    owner_type: CartOwnerType
    customer_id: UUID | None
    session_id: str | None
    status: CartStatus
    currency: str
    version: int


class CartLineCreateRequest(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)
    currency: str = Field(
        min_length=3,
        max_length=3,
    )


class CartLineResponse(BaseModel):
    id: UUID
    cart_id: UUID
    product_id: UUID
    variant_id: UUID | None
    listing_id: UUID | None
    quantity: int
    unit_price: Decimal
    currency: str


class QuantityUpdateRequest(BaseModel):
    quantity: int = Field(ge=1)


class CartTotalsResponse(BaseModel):
    subtotal: Decimal
    item_count: int
    currency: str
