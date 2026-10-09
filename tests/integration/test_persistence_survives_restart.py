from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer, MerchantProduct
from database.models.commerce_feedback import WardrobeItem
from database.models.identity import User
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@pytest_asyncio.fixture
async def shared_db_factory() -> async_sessionmaker[AsyncSession]:
    # Shared in-memory database using StaticPool to simulate persistent database across restarts
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_data_survives_server_restart(shared_db_factory) -> None:
    """Simulates server restart: write data in instance 1, close, read back in fresh instance 2."""
    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    product_id = uuid4()

    # --- Server Instance 1: Ingest catalog and user profile ---
    profile_uow_1 = ProfileUnitOfWork(shared_db_factory)
    catalog_uow_1 = CatalogUnitOfWork(shared_db_factory)
    wardrobe_uow_1 = CommerceWardrobeUnitOfWork(shared_db_factory)

    async with profile_uow_1:
        profile_uow_1.users.add(User(id=user_id))
        await profile_uow_1.body_profiles.upsert(
            user_id=user_id, height_cm=182, weight_kg=78, build="athletic"
        )
        await profile_uow_1.preferences.upsert(
            user_id=user_id,
            colors_favored=["emerald", "black"],
            categories=["outerwear", "shirts"],
            budget_max=10000,
        )
        await profile_uow_1.commit()

    async with catalog_uow_1:
        merchant = Merchant(id=merchant_id, name="Nordic Studio", merchant_type="brand")
        catalog_uow_1.merchants.add(merchant)
        product = MerchantProduct(
            id=product_id,
            merchant_id=merchant_id,
            source_product_id="NS-001",
            title="Wool Overcoat",
            source_url="https://nordic.studio/p/001",
        )
        catalog_uow_1.products.add(product)
        garment = CanonicalGarment(id=garment_id, category="outerwear", subcategory="coat")
        catalog_uow_1.canonical_garments.add(garment)
        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id="NS-001",
            url="https://nordic.studio/p/001",
            price_minor=899900,
            currency="INR",
        )
        catalog_uow_1.offers.add(offer)
        await catalog_uow_1.commit()

    async with wardrobe_uow_1:
        wardrobe_uow_1.wardrobe.add(
            WardrobeItem(
                id=uuid4(),
                user_id=user_id,
                garment_id=garment_id,
                snapshot_title="Wool Overcoat",
                snapshot_price_minor=899900,
                snapshot_currency="INR",
                snapshot_image_key="garments/coat.jpg",
            )
        )
        await wardrobe_uow_1.commit()

    # --- Simulate Restart: All session/UoW references dropped ---
    del profile_uow_1
    del catalog_uow_1
    del wardrobe_uow_1

    # --- Server Instance 2: Fresh UoW instances query data ---
    profile_uow_2 = ProfileUnitOfWork(shared_db_factory)
    catalog_uow_2 = CatalogUnitOfWork(shared_db_factory)
    wardrobe_uow_2 = CommerceWardrobeUnitOfWork(shared_db_factory)

    async with profile_uow_2:
        body = await profile_uow_2.body_profiles.get_by_user_id(user_id)
        assert body is not None
        assert body.height_cm == 182
        assert body.build == "athletic"

        pref = await profile_uow_2.preferences.get_by_user_id(user_id)
        assert pref is not None
        assert pref.colors_favored == ["emerald", "black"]
        assert pref.budget_max == 10000

    async with catalog_uow_2:
        garment_found = await catalog_uow_2.canonical_garments.get_by_id(garment_id)
        assert garment_found is not None
        assert garment_found.category == "outerwear"

    async with wardrobe_uow_2:
        items = await wardrobe_uow_2.wardrobe.list_for_user(user_id)
        assert len(items) == 1
        assert items[0].snapshot_title == "Wool Overcoat"
        assert items[0].snapshot_price_minor == 899900
