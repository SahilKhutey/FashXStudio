from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from api.app.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.errors import EntityNotFoundError
from api.app.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from database.models.catalog import Merchant


@pytest.mark.asyncio
async def test_affiliate_handoff_and_tracking_id(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(session_factory)

    # 1. Setup User and Product
    create_uc = CreateProfileUseCase(profile_uow)
    user = await create_uc.execute(CreateProfileCommand(height_cm=170, weight_kg=65))
    user_id = user.user_id

    async with catalog_uow:
        merchant = Merchant(name="Myntra Direct", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="MYN-4921",
            title="Slim Fit Denim Jeans",
            source_url="https://myntra.com/jeans/4921?color=indigo",
            category="bottoms",
            price_minor=299900,
        )
    )
    garment_id = product.canonical_garment_id

    async with catalog_uow:
        offers = await catalog_uow.offers.list_for_garment(garment_id)
        offer_id = offers[0].id

    # 2. Execute Outbound Buy Click (Rule I12)
    click_uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)
    click_res = await click_uc.execute(
        CreateBuyClickCommand(
            user_id=user_id,
            garment_id=garment_id,
            offer_id=offer_id,
        )
    )

    assert click_res.buy_click_id is not None
    assert "fashx_" in click_res.tracking_id

    # 3. Verify Enriched URL Attribution Parameters
    parsed = urlparse(click_res.redirect_url)
    assert parsed.netloc == "myntra.com"
    params = parse_qs(parsed.query)

    assert params.get("color") == ["indigo"]  # Preserved original query param
    assert params.get("utm_source") == ["fashx"]
    assert params.get("utm_medium") == ["app"]
    assert params.get("utm_campaign") == ["vto_purchase"]
    assert params.get("sub_id") == [click_res.tracking_id]
    assert params.get("click_id") == [str(click_res.buy_click_id)]

    # 4. Verify Non-Existent Offer Fails
    with pytest.raises(EntityNotFoundError):
        await click_uc.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=uuid4(),
            )
        )
