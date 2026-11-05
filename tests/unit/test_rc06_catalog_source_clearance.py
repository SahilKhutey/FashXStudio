from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import ValidationError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@pytest.fixture
async def db_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("status,should_pass", [
    ("cleared", True),
    ("pending", False),
    ("revoked", False),
    ("review", False),
])
async def test_rc06_source_clearance_policy(db_session_factory, status, should_pass):
    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    source_id = uuid4()
    offer_id = uuid4()

    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_id, display_name="Linen Shirt", category="tops", active=True, price_minor=1000)
        )
        catalog_uow.merchants.add(Merchant(id=merchant_id, name="Retailer", merchant_type="retailer"))
        source = CatalogSource(
            id=source_id,
            slug=f"source-{status}",
            name=f"Source {status}",
            kind="manual",
            status=status,
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        catalog_uow.merchant_products.add(
            MerchantProduct(
                id=uuid4(),
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id="SKU-1",
                title="Linen Shirt",
                source_url="https://www.retailer.com/sku-1",
            )
        )
        catalog_uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="SKU-1",
                url="https://www.retailer.com/sku-1",
                price_minor=1000,
                in_stock=True,
            )
        )
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=commerce_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        allowed_hosts={"retailer.com"},
    )
    cmd = CreateBuyClickCommand(user_id=user_id, garment_id=garment_id, offer_id=offer_id)

    if should_pass:
        res = await use_case.execute(cmd)
        assert res.redirect_url.startswith("https://www.retailer.com/sku-1")
    else:
        with pytest.raises(ValidationError) as exc:
            await use_case.execute(cmd)
        assert "not cleared" in str(exc.value)
