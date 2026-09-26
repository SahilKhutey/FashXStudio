from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus
from app.domain.pricing.entities import Price, PricingRule
from app.domain.pricing.enums import (
    DiscountType,
    PriceStatus,
    PriceType,
    RuleStatus,
)
from app.domain.pricing.events import (
    PriceCalculated,
    PriceCreated,
    PricingRuleCreated,
)
from app.domain.pricing.rules import PricingContext
from app.domain.pricing.service import PricingService
from app.repositories.pricing.memory import (
    InMemoryPriceRepository,
    InMemoryPricingRuleRepository,
)


@pytest.fixture
def service_setup():
    price_repo = InMemoryPriceRepository()
    rule_repo = InMemoryPricingRuleRepository()
    event_bus = EventBus()
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    for event_name in ["PriceCreated", "PricingRuleCreated", "PriceCalculated"]:
        event_bus.subscribe(event_name, handler)

    service = PricingService(
        price_repository=price_repo,
        rule_repository=rule_repo,
        event_bus=event_bus,
    )
    return service, price_repo, rule_repo, events


@pytest.mark.asyncio
async def test_create_price(service_setup):
    service, price_repo, _, events = service_setup
    context = CoreContext.create()

    price = Price(
        product_id=uuid4(),
        amount=Decimal("199.99"),
        price_type=PriceType.BASE,
        status=PriceStatus.ACTIVE,
    )

    created = await service.create_price(context=context, price=price)
    assert created.id == price.id

    saved = await price_repo.get(price.id)
    assert saved is not None
    assert saved.amount == Decimal("199.99")

    price_events = [e for e in events if isinstance(e, PriceCreated)]
    assert len(price_events) == 1
    assert price_events[0].entity_id == price.id


@pytest.mark.asyncio
async def test_create_rule(service_setup):
    service, _, rule_repo, events = service_setup
    context = CoreContext.create()

    rule = PricingRule(
        name="Flat Discount",
        status=RuleStatus.ACTIVE,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("50.00"),
    )

    created = await service.create_rule(context=context, rule=rule)
    assert created.id == rule.id

    saved = await rule_repo.get(rule.id)
    assert saved is not None
    assert saved.name == "Flat Discount"

    rule_events = [e for e in events if isinstance(e, PricingRuleCreated)]
    assert len(rule_events) == 1
    assert rule_events[0].entity_id == rule.id


@pytest.mark.asyncio
async def test_calculate_no_price_raises_not_found(service_setup):
    service, _, _, _ = service_setup
    context = CoreContext.create()
    pricing_context = PricingContext(
        product_id=uuid4(),
    )

    with pytest.raises(NotFoundError, match="No active price was found"):
        await service.calculate(context=context, pricing_context=pricing_context)


@pytest.mark.asyncio
async def test_calculate_base_price_with_quantity(service_setup):
    service, price_repo, _, events = service_setup
    context = CoreContext.create()
    product_id = uuid4()

    price = Price(
        product_id=product_id,
        amount=Decimal("150.00"),
        status=PriceStatus.ACTIVE,
    )
    await price_repo.save(price)

    pricing_context = PricingContext(
        product_id=product_id,
        quantity=3,
    )

    breakdown = await service.calculate(
        context=context,
        pricing_context=pricing_context,
    )

    assert breakdown.original_amount == Decimal("450.00")
    assert breakdown.final_amount == Decimal("450.00")
    assert len(breakdown.adjustments) == 0

    calc_events = [e for e in events if isinstance(e, PriceCalculated)]
    assert len(calc_events) == 1
    assert calc_events[0].entity_id == price.id


@pytest.mark.asyncio
async def test_calculate_with_rules_and_priority(service_setup):
    service, price_repo, rule_repo, _ = service_setup
    context = CoreContext.create()
    product_id = uuid4()

    price = Price(
        product_id=product_id,
        amount=Decimal("1000.00"),
        status=PriceStatus.ACTIVE,
    )
    await price_repo.save(price)

    # Rule 1: Priority 10 -> 10% off (1000 -> 900)
    rule1 = PricingRule(
        name="10% Off",
        product_id=product_id,
        status=RuleStatus.ACTIVE,
        priority=10,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )
    # Rule 2: Priority 20 -> Fixed 100 off (900 -> 800)
    rule2 = PricingRule(
        name="100 Off",
        product_id=product_id,
        status=RuleStatus.ACTIVE,
        priority=20,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("100"),
    )
    # Rule 3: Priority 30 -> requires min qty 5 (skipped for qty 1)
    rule3 = PricingRule(
        name="Bulk Promo",
        product_id=product_id,
        status=RuleStatus.ACTIVE,
        priority=30,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("50"),
        minimum_quantity=5,
    )

    await rule_repo.save(rule1)
    await rule_repo.save(rule2)
    await rule_repo.save(rule3)

    pricing_context = PricingContext(
        product_id=product_id,
        quantity=1,
    )

    breakdown = await service.calculate(
        context=context,
        pricing_context=pricing_context,
    )

    assert breakdown.original_amount == Decimal("1000.00")
    assert breakdown.final_amount == Decimal("800.00")
    assert len(breakdown.adjustments) == 2
    assert breakdown.adjustments[0].rule_id == rule1.id
    assert breakdown.adjustments[0].amount == Decimal("-100.00")
    assert breakdown.adjustments[1].rule_id == rule2.id
    assert breakdown.adjustments[1].amount == Decimal("-100.00")
