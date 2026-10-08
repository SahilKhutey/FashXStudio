from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from fashx.core.context import CoreContext
from fashx.core.errors import NotFoundError
from fashx.core.event_bus import EventBus

from .entities import Price, PricingRule
from .events import (
    PriceCalculated,
    PriceCreated,
    PricingRuleCreated,
)
from .repository import (
    PriceRepository,
    PricingRuleRepository,
)
from .rules import (
    PriceAdjustment,
    PriceBreakdown,
    PricingContext,
    calculate_discount,
    money,
    rule_matches,
    rule_valid_at,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class PricingService:
    price_repository: PriceRepository
    rule_repository: PricingRuleRepository
    event_bus: EventBus

    async def create_price(
        self,
        *,
        context: CoreContext,
        price: Price,
    ) -> Price:
        price.validate()

        await self.price_repository.save(price)

        await self.event_bus.publish(
            PriceCreated(
                entity_id=price.id,
                correlation_id=context.correlation_id,
            )
        )

        return price

    async def create_rule(
        self,
        *,
        context: CoreContext,
        rule: PricingRule,
    ) -> PricingRule:
        rule.validate()

        await self.rule_repository.save(rule)

        await self.event_bus.publish(
            PricingRuleCreated(
                entity_id=rule.id,
                correlation_id=context.correlation_id,
            )
        )

        return rule

    async def calculate(
        self,
        *,
        context: CoreContext,
        pricing_context: PricingContext,
    ) -> PriceBreakdown:
        timestamp = (
            pricing_context.timestamp
            or utc_now()
        )

        prices = await self.price_repository.list_for_target(
            product_id=pricing_context.product_id,
            variant_id=pricing_context.variant_id,
            listing_id=pricing_context.listing_id,
        )

        valid_prices = [
            price
            for price in prices
            if price.is_valid_at(timestamp)
            and price.currency.upper() == pricing_context.currency.upper()
        ]

        if not valid_prices:
            raise NotFoundError("No active price was found.")

        valid_prices.sort(
            key=lambda item: (
                item.price_type.value,
                item.created_at,
            )
        )

        selected_price = valid_prices[0]

        original_amount = money(
            selected_price.amount * pricing_context.quantity
        )

        current_amount = original_amount

        rules = await self.rule_repository.list_active()

        applicable_rules = [
            rule
            for rule in rules
            if rule_valid_at(rule, timestamp)
            and rule_matches(rule, pricing_context)
        ]

        applicable_rules.sort(key=lambda rule: rule.priority)

        adjustments: list[PriceAdjustment] = []

        for rule in applicable_rules:
            discount = calculate_discount(current_amount, rule)

            if discount <= Decimal("0"):
                continue

            current_amount = money(current_amount - discount)

            adjustments.append(
                PriceAdjustment(
                    rule_id=rule.id,
                    description=rule.name,
                    amount=-discount,
                )
            )

        breakdown = PriceBreakdown(
            original_amount=original_amount,
            adjustments=tuple(adjustments),
            final_amount=money(current_amount),
            currency=selected_price.currency,
        )

        await self.event_bus.publish(
            PriceCalculated(
                entity_id=selected_price.id,
                correlation_id=context.correlation_id,
            )
        )

        return breakdown
