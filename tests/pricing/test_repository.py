from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.pricing.entities import Price, PricingRule
from app.domain.pricing.enums import PriceStatus, PriceType, RuleStatus
from app.repositories.pricing.memory import (
    InMemoryPriceRepository,
    InMemoryPricingRuleRepository,
)


@pytest.mark.asyncio
async def test_in_memory_price_repository():
    repo = InMemoryPriceRepository()
    product_id = uuid4()
    variant_id = uuid4()

    price1 = Price(
        product_id=product_id,
        amount=Decimal("100.00"),
        price_type=PriceType.BASE,
        status=PriceStatus.ACTIVE,
    )
    price2 = Price(
        product_id=product_id,
        variant_id=variant_id,
        amount=Decimal("120.00"),
        price_type=PriceType.BASE,
        status=PriceStatus.ACTIVE,
    )
    other_price = Price(
        product_id=uuid4(),
        amount=Decimal("50.00"),
    )

    await repo.save(price1)
    await repo.save(price2)
    await repo.save(other_price)

    fetched = await repo.get(price1.id)
    assert fetched is not None
    assert fetched.id == price1.id

    # List for product only
    target_prices = await repo.list_for_target(product_id=product_id)
    assert len(target_prices) == 2

    # List for specific variant
    variant_prices = await repo.list_for_target(
        product_id=product_id,
        variant_id=variant_id,
    )
    assert len(variant_prices) == 1
    assert variant_prices[0].id == price2.id


@pytest.mark.asyncio
async def test_in_memory_pricing_rule_repository():
    repo = InMemoryPricingRuleRepository()

    active_rule = PricingRule(
        name="Active Promo",
        status=RuleStatus.ACTIVE,
        discount_value=Decimal("10.00"),
    )
    draft_rule = PricingRule(
        name="Draft Promo",
        status=RuleStatus.DRAFT,
        discount_value=Decimal("20.00"),
    )

    await repo.save(active_rule)
    await repo.save(draft_rule)

    fetched = await repo.get(active_rule.id)
    assert fetched is not None
    assert fetched.name == "Active Promo"

    active_rules = await repo.list_active()
    assert len(active_rules) == 1
    assert active_rules[0].id == active_rule.id
