from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import (
    DiscountType,
    PriceStatus,
    PriceType,
    RuleScope,
    RuleStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Price:
    id: UUID = field(default_factory=new_id)
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    amount: Decimal = Decimal("0.00")
    currency: str = "INR"
    price_type: PriceType = PriceType.BASE
    status: PriceStatus = PriceStatus.DRAFT
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if (
            self.product_id is None
            and self.variant_id is None
            and self.listing_id is None
        ):
            raise ValidationError(
                "Price requires product, variant, or listing."
            )

        if self.amount < Decimal("0"):
            raise ValidationError(
                "Price amount cannot be negative."
            )

        if len(self.currency) != 3:
            raise ValidationError(
                "Currency must be a 3-character code."
            )

        if (
            self.valid_from
            and self.valid_until
            and self.valid_until <= self.valid_from
        ):
            raise ValidationError(
                "Price validity window is invalid."
            )

        if self.version < 1:
            raise ValidationError(
                "Price version must be positive."
            )

    def is_valid_at(
        self,
        timestamp: datetime,
    ) -> bool:
        if self.status != PriceStatus.ACTIVE:
            return False

        if (
            self.valid_from
            and timestamp < self.valid_from
        ):
            return False

        if (
            self.valid_until
            and timestamp >= self.valid_until
        ):
            return False

        return True

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class PricingRule:
    id: UUID = field(default_factory=new_id)
    name: str = ""
    scope: RuleScope = RuleScope.PRODUCT
    status: RuleStatus = RuleStatus.DRAFT
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: Decimal = Decimal("0.00")
    priority: int = 100
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    region: str | None = None
    minimum_quantity: int | None = None
    minimum_cart_value: Decimal | None = None
    customer_id: UUID | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "Pricing rule name is required."
            )

        if self.discount_value < Decimal("0"):
            raise ValidationError(
                "Discount value cannot be negative."
            )

        if (
            self.discount_type == DiscountType.PERCENTAGE
            and self.discount_value > Decimal("100")
        ):
            raise ValidationError(
                "Percentage discount cannot exceed 100."
            )

        if (
            self.minimum_quantity is not None
            and self.minimum_quantity < 1
        ):
            raise ValidationError(
                "Minimum quantity must be positive."
            )

        if (
            self.minimum_cart_value is not None
            and self.minimum_cart_value < Decimal("0")
        ):
            raise ValidationError(
                "Minimum cart value cannot be negative."
            )

        if self.priority < 0:
            raise ValidationError(
                "Priority cannot be negative."
            )

        if (
            self.valid_from
            and self.valid_until
            and self.valid_until <= self.valid_from
        ):
            raise ValidationError(
                "Rule validity window is invalid."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
