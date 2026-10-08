from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fashx.core.contracts import Entity
from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import (
    CartLineStatus,
    CartOwnerType,
    CartStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CartLine:
    id: UUID = field(default_factory=new_id)
    cart_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    currency: str = "INR"
    status: CartLineStatus = CartLineStatus.ACTIVE
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.cart_id is None:
            raise ValidationError("Cart line requires cart ID.")

        if self.product_id is None:
            raise ValidationError("Cart line requires product ID.")

        if self.quantity < 1:
            raise ValidationError("Cart line quantity must be at least 1.")

        if self.unit_price < 0:
            raise ValidationError("Cart line price cannot be negative.")

        if not self.currency.strip():
            raise ValidationError("Cart line requires currency.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)

    def update_quantity(self, quantity: int) -> None:
        if quantity < 1:
            raise ValidationError("Quantity must be at least 1.")

        self.quantity = quantity
        self.updated_at = utc_now()

    def remove(self) -> None:
        self.status = CartLineStatus.REMOVED
        self.updated_at = utc_now()


@dataclass(slots=True)
class Cart(Entity):
    id: UUID = field(default_factory=new_id)
    owner_type: CartOwnerType = CartOwnerType.ANONYMOUS
    customer_id: UUID | None = None
    session_id: str | None = None
    status: CartStatus = CartStatus.ACTIVE
    currency: str = "INR"
    expires_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if (
            self.owner_type == CartOwnerType.CUSTOMER
            and self.customer_id is None
        ):
            raise ValidationError("Customer cart requires customer ID.")

        if (
            self.owner_type == CartOwnerType.ANONYMOUS
            and not self.session_id
        ):
            raise ValidationError("Anonymous cart requires session ID.")

        if not self.currency.strip():
            raise ValidationError("Cart requires currency.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")

        if self.version < 1:
            raise ValidationError("Cart version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1

    def is_expired(self, at: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False

        now = at or utc_now()
        return now >= self.expires_at
