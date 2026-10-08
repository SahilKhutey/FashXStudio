from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ConflictError
from fashx.domain.promotions.entities import (
    Offer,
    Promotion,
)
from fashx.domain.promotions.enums import (
    DiscountType,
    PromotionScope,
)
from fashx.repositories.promotions.memory import (
    InMemoryOfferRepository,
    InMemoryPromotionRepository,
)


@pytest.mark.asyncio
async def test_promotion_save_get():
    repository = InMemoryPromotionRepository()

    promotion = Promotion(
        name="Festival",
        code="FEST20",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
    )

    await repository.save(promotion)

    result = await repository.get(promotion.id)
    assert result is promotion


@pytest.mark.asyncio
async def test_promotion_code_lookup():
    repository = InMemoryPromotionRepository()

    promotion = Promotion(
        name="Festival",
        code="FEST20",
        scope=PromotionScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
    )

    await repository.save(promotion)

    result = await repository.get_by_code("fest20")
    assert result is promotion


@pytest.mark.asyncio
async def test_promotion_code_conflict():
    repository = InMemoryPromotionRepository()

    p1 = Promotion(
        name="Promo 1",
        code="PROMO_SAME",
    )
    p2 = Promotion(
        name="Promo 2",
        code="PROMO_SAME",
    )

    await repository.save(p1)
    with pytest.raises(ConflictError):
        await repository.save(p2)


@pytest.mark.asyncio
async def test_offer_save_and_lookups():
    repo = InMemoryOfferRepository()
    promo_id = uuid4()
    prod_id = uuid4()
    var_id = uuid4()
    list_id = uuid4()

    offer_prod = Offer(promotion_id=promo_id, product_id=prod_id)
    offer_var = Offer(promotion_id=promo_id, variant_id=var_id)
    offer_list = Offer(promotion_id=promo_id, listing_id=list_id)

    await repo.save(offer_prod)
    await repo.save(offer_var)
    await repo.save(offer_list)

    assert len(await repo.list_by_product(prod_id)) == 1
    assert len(await repo.list_by_variant(var_id)) == 1
    assert len(await repo.list_by_listing(list_id)) == 1
