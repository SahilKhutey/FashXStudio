from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    CheckoutStatus,
    OrderLineStatus,
    OrderStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CheckoutSession:
    id: UUID = field(default_factory=new_id)
    cart_id: UUID | None = None
    customer_id: UUID | None = None
    email: str | None = None
    status: CheckoutStatus = CheckoutStatus.CREATED
    idempotency_key: str | None = None
    currency: str = "INR"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.cart_id is None:
            raise ValidationError("Checkout requires cart ID.")

        if self.customer_id is None and not self.email:
            raise ValidationError(
                "Checkout requires customer ID or email."
            )

        if not self.currency.strip():
            raise ValidationError("Checkout requires currency.")

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be a 3-character code."
            )

        if self.version < 1:
            raise ValidationError(
                "Checkout version must be positive."
            )


@dataclass(slots=True)
class OrderLine:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    currency: str = "INR"
    status: OrderLineStatus = OrderLineStatus.ACTIVE
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Order line requires order ID.")

        if self.product_id is None:
            raise ValidationError("Order line requires product ID.")

        if self.quantity < 1:
            raise ValidationError(
                "Order line quantity must be at least 1."
            )

        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative.")

        if self.discount < 0:
            raise ValidationError("Discount cannot be negative.")

        if self.discount > self.unit_price:
            raise ValidationError(
                "Discount cannot exceed unit price."
            )

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be a 3-character code."
            )

    @property
    def subtotal(self) -> Decimal:
        gross = self.unit_price * Decimal(self.quantity)
        discount = self.discount * Decimal(self.quantity)
        return max(
            gross - discount,
            Decimal("0"),
        )


@dataclass(slots=True)
class Order:
    id: UUID = field(default_factory=new_id)
    order_number: str = ""
    checkout_id: UUID | None = None
    cart_id: UUID | None = None
    customer_id: UUID | None = None
    email: str | None = None
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    currency: str = "INR"
    subtotal: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if not self.order_number.strip():
            raise ValidationError("Order number is required.")

        if self.checkout_id is None:
            raise ValidationError("Order requires checkout ID.")

        if self.cart_id is None:
            raise ValidationError("Order requires cart ID.")

        if not self.email:
            raise ValidationError("Order requires email.")

        if self.subtotal < 0:
            raise ValidationError("Subtotal cannot be negative.")

        if self.discount < 0:
            raise ValidationError("Discount cannot be negative.")

        if self.total < 0:
            raise ValidationError("Total cannot be negative.")

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be a 3-character code."
            )

        if self.version < 1:
            raise ValidationError("Order version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
