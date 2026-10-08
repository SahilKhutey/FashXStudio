from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import ValidationError
from app.core.event_bus import EventBus
from fashx.domain.pricing.enums import Currency
from fashx.domain.pricing.money import money
from fashx.domain.promotions.entities import (
    Offer,
    Promotion,
)
from fashx.domain.promotions.enums import (
    DiscountType,
    OfferStatus,
    PromotionScope,
    PromotionStatus,
)
from fashx.domain.promotions.service import (
    PromotionService,
)
from fashx.repositories.promotions.memory import (
    InMemoryOfferRepository,
    InMemoryPromotionRepository,
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def service(event_bus):
    return PromotionService(
        promotion_repository=InMemoryPromotionRepository(),
        offer_repository=InMemoryOfferRepository(),
        event_bus=event_bus,
    )


@pytest.mark.asyncio
async def test_create_promotion(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PromotionCreated", handler)

    promotion = await service.create_promotion(
        context=CoreContext.create(),
        promotion=Promotion(
            name="Festival Sale",
            scope=PromotionScope.PRODUCT,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
        ),
    )

    assert promotion.name == "Festival Sale"
    assert len(events) == 1
    assert events[0].entity_id == promotion.id


@pytest.mark.asyncio
async def test_calculate_offer(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PromotionApplied", handler)

    promotion = await service.create_promotion(
        context=CoreContext.create(),
        promotion=Promotion(
            name="20 Percent Sale",
            scope=PromotionScope.PRODUCT,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
        ),
    )

    await service.change_promotion_status(
        context=CoreContext.create(),
        promotion_id=promotion.id,
        target=PromotionStatus.ACTIVE,
    )

    offer = await service.create_offer(
        context=CoreContext.create(),
        offer=Offer(
            promotion_id=promotion.id,
            product_id=uuid4(),
        ),
    )

    await service.change_offer_status(
        context=CoreContext.create(),
        offer_id=offer.id,
        target=OfferStatus.ACTIVE,
    )

    result = await service.calculate_offer(
        context=CoreContext.create(),
        offer_id=offer.id,
        base_price=money(
            "2000",
            Currency.INR,
        ),
    )

    assert result.discount.amount == Decimal("400.00")
    assert result.final_price.amount == Decimal("1600.00")
    assert len(events) == 1


@pytest.mark.asyncio
async def test_calculate_offer_inactive_offer(service):
    promotion = await service.create_promotion(
        context=CoreContext.create(),
        promotion=Promotion(
            name="Sale",
            scope=PromotionScope.PRODUCT,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
        ),
    )
    await service.change_promotion_status(
        context=CoreContext.create(),
        promotion_id=promotion.id,
        target=PromotionStatus.ACTIVE,
    )

    offer = await service.create_offer(
        context=CoreContext.create(),
        offer=Offer(
            promotion_id=promotion.id,
            product_id=uuid4(),
        ),
    )  # Status is DRAFT

    result = await service.calculate_offer(
        context=CoreContext.create(),
        offer_id=offer.id,
        base_price=money("2000", Currency.INR),
    )

    assert result.discount.amount == Decimal("0.00")
    assert result.final_price.amount == Decimal("2000.00")


@pytest.mark.asyncio
async def test_calculate_offer_minimum_purchase(service):
    promotion = await service.create_promotion(
        context=CoreContext.create(),
        promotion=Promotion(
            name="Min Purchase Sale",
            scope=PromotionScope.PRODUCT,
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("500"),
            minimum_purchase_value=Decimal("2000"),
        ),
    )
    await service.change_promotion_status(
        context=CoreContext.create(),
        promotion_id=promotion.id,
        target=PromotionStatus.ACTIVE,
    )

    offer = await service.create_offer(
        context=CoreContext.create(),
        offer=Offer(
            promotion_id=promotion.id,
            product_id=uuid4(),
        ),
    )
    await service.change_offer_status(
        context=CoreContext.create(),
        offer_id=offer.id,
        target=OfferStatus.ACTIVE,
    )

    # Ineligible (purchase_value < 2000)
    ineligible = await service.calculate_offer(
        context=CoreContext.create(),
        offer_id=offer.id,
        base_price=money("2000", Currency.INR),
        purchase_value=Decimal("1500"),
    )
    assert ineligible.discount.amount == Decimal("0.00")
    assert ineligible.final_price.amount == Decimal("2000.00")

    # Eligible (purchase_value >= 2000)
    eligible = await service.calculate_offer(
        context=CoreContext.create(),
        offer_id=offer.id,
        base_price=money("2000", Currency.INR),
        purchase_value=Decimal("2500"),
    )
    assert eligible.discount.amount == Decimal("500.00")
    assert eligible.final_price.amount == Decimal("1500.00")


@pytest.mark.asyncio
async def test_create_offer_archived_promotion_rejected(service):
    promotion = await service.create_promotion(
        context=CoreContext.create(),
        promotion=Promotion(
            name="Sale",
            scope=PromotionScope.PRODUCT,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
        ),
    )
    await service.change_promotion_status(
        context=CoreContext.create(),
        promotion_id=promotion.id,
        target=PromotionStatus.ARCHIVED,
    )

    with pytest.raises(ValidationError):
        await service.create_offer(
            context=CoreContext.create(),
            offer=Offer(
                promotion_id=promotion.id,
                product_id=uuid4(),
            ),
        )
