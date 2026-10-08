from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from .entities import PricingRule
from .enums import DiscountType, RuleStatus

MONEY_QUANTUM = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


@dataclass(frozen=True, slots=True)
class PricingContext:
    product_id: UUID
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    customer_id: UUID | None = None
    region: str | None = None
    currency: str = "INR"
    quantity: int = 1
    cart_value: Decimal = Decimal("0.00")
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class PriceAdjustment:
    rule_id: UUID | None
    description: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class PriceBreakdown:
    original_amount: Decimal
    adjustments: tuple[PriceAdjustment, ...]
    final_amount: Decimal
    currency: str


def calculate_discount(
    amount: Decimal,
    rule: PricingRule,
) -> Decimal:
    if rule.discount_type == DiscountType.PERCENTAGE:
        discount = (
            amount
            * rule.discount_value
            / Decimal("100")
        )
    else:
        discount = rule.discount_value

    if discount > amount:
        discount = amount

    return money(discount)


def rule_matches(
    rule: PricingRule,
    context: PricingContext,
) -> bool:
    if rule.product_id is not None:
        if rule.product_id != context.product_id:
            return False

    if rule.variant_id is not None:
        if rule.variant_id != context.variant_id:
            return False

    if rule.listing_id is not None:
        if rule.listing_id != context.listing_id:
            return False

    if rule.customer_id is not None:
        if rule.customer_id != context.customer_id:
            return False

    if rule.region is not None:
        if (
            context.region is None
            or rule.region.upper() != context.region.upper()
        ):
            return False

    if (
        rule.minimum_quantity is not None
        and context.quantity < rule.minimum_quantity
    ):
        return False

    if (
        rule.minimum_cart_value is not None
        and context.cart_value < rule.minimum_cart_value
    ):
        return False

    return True


def rule_valid_at(
    rule: PricingRule,
    timestamp: datetime,
) -> bool:
    if rule.status != RuleStatus.ACTIVE:
        return False

    if rule.valid_from and timestamp < rule.valid_from:
        return False

    if rule.valid_until and timestamp >= rule.valid_until:
        return False

    return True
