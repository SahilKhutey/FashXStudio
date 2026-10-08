from uuid import UUID

from fashx.domain.pricing.entities import (
    Price,
    PricingRule,
)
from fashx.domain.pricing.repository import (
    PriceRepository,
    PricingRuleRepository,
)


class InMemoryPriceRepository(PriceRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Price] = {}

    async def get(self, price_id: UUID) -> Price | None:
        return self._items.get(price_id)

    async def save(self, price: Price) -> Price:
        self._items[price.id] = price
        return price

    async def list_for_target(
        self,
        *,
        product_id: UUID,
        variant_id: UUID | None = None,
        listing_id: UUID | None = None,
    ) -> list[Price]:
        return [
            price
            for price in self._items.values()
            if (
                price.product_id == product_id
                and (variant_id is None or price.variant_id == variant_id)
                and (listing_id is None or price.listing_id == listing_id)
            )
        ]


class InMemoryPricingRuleRepository(PricingRuleRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, PricingRule] = {}

    async def get(self, rule_id: UUID) -> PricingRule | None:
        return self._items.get(rule_id)

    async def save(self, rule: PricingRule) -> PricingRule:
        self._items[rule.id] = rule
        return rule

    async def list_active(self) -> list[PricingRule]:
        return [
            rule
            for rule in self._items.values()
            if rule.status.value == "active"
        ]
