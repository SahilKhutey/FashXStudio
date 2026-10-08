from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import (
    OrderLineStatus,
    OrderStatus,
)

MONEY_QUANTUM = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_order_number() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"FX-{timestamp}"


@dataclass(frozen=True, slots=True)
class OrderAddressSnapshot:
    recipient_name: str
    address_line_1: str
    address_line_2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "IN"
    phone: str | None = None

    def validate(self) -> None:
        required = {
            "recipient_name": self.recipient_name,
            "address_line_1": self.address_line_1,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }

        for name, value in required.items():
            if not value.strip():
                raise ValidationError(f"{name} is required.")


@dataclass(slots=True)
class OrderLine:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    title: str = ""
    sku: str | None = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
    currency: str = "INR"
    discount: Decimal = Decimal("0.00")
    subtotal: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    status: OrderLineStatus = OrderLineStatus.PENDING
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def calculate(self) -> None:
        self.subtotal = money(self.unit_price * Decimal(self.quantity))
        self.total = money(max(Decimal("0.00"), self.subtotal - self.discount))
        self.updated_at = utc_now()

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError("Order line requires order_id.")

        if self.product_id is None:
            raise ValidationError("Order line requires product_id.")

        if not self.title.strip():
            raise ValidationError("Order line title is required.")

        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1.")

        if self.unit_price < Decimal("0"):
            raise ValidationError("Unit price cannot be negative.")

        if self.discount < Decimal("0"):
            raise ValidationError("Discount cannot be negative.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be 3 characters.")

        self.calculate()


@dataclass(slots=True)
class Order:
    id: UUID = field(default_factory=new_id)
    order_number: str = ""
    customer_id: UUID | None = None
    status: OrderStatus = OrderStatus.PENDING
    currency: str = "INR"
    billing_address: OrderAddressSnapshot | None = None
    shipping_address: OrderAddressSnapshot | None = None
    subtotal: Decimal = Decimal("0.00")
    discount_total: Decimal = Decimal("0.00")
    shipping_total: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    # Backward compatibility fields
    checkout_id: UUID | None = None
    cart_id: UUID | None = None
    email: str | None = None
    total: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if self.total > Decimal("0") and self.grand_total == Decimal("0"):
            self.grand_total = self.total
        elif self.grand_total > Decimal("0") and self.total == Decimal("0"):
            self.total = self.grand_total

    def validate(self) -> None:
        if not self.order_number.strip():
            raise ValidationError("Order number is required.")

        if self.shipping_address is None:
            raise ValidationError("Shipping address is required.")

        self.shipping_address.validate()

        if self.billing_address:
            self.billing_address.validate()

        if len(self.currency) != 3:
            raise ValidationError("Currency must be 3 characters.")

        if self.version < 1:
            raise ValidationError("Order version must be positive.")

    def calculate_totals(
        self,
        lines: list[OrderLine],
    ) -> None:
        self.subtotal = money(
            sum(
                (line.subtotal for line in lines),
                Decimal("0.00"),
            )
        )

        self.discount_total = money(
            sum(
                (line.discount for line in lines),
                Decimal("0.00"),
            )
        )

        self.grand_total = money(
            self.subtotal
            - self.discount_total
            + self.shipping_total
            + self.tax_total
        )
        self.total = self.grand_total
        self.updated_at = utc_now()

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
