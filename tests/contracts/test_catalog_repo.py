from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer, MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
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
async def test_catalog_ingest_and_retrieval(session_factory) -> None:
    uow = CatalogUnitOfWork(session_factory)
    merchant_id = uuid4()
    product_id = uuid4()
    garment_id = uuid4()
    offer_id = uuid4()

    async with uow:
        merchant = Merchant(id=merchant_id, name="Zara India", merchant_type="affiliate")
        uow.merchants.add(merchant)

        product = MerchantProduct(
            id=product_id,
            merchant_id=merchant_id,
            source_product_id="Z12345",
            title="Linen Shirt",
            source_url="https://zara.com/in/12345",
        )
        uow.products.add(product)

        garment = CanonicalGarment(
            id=garment_id,
            category="tops",
            subcategory="shirt",
        )
        uow.canonical_garments.add(garment)

        offer = MerchantOffer(
            id=offer_id,
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id="Z12345",
            url="https://zara.com/in/12345",
            price_minor=299000,
            currency="INR",
        )
        uow.offers.add(offer)
        await uow.commit()

    verify_uow = CatalogUnitOfWork(session_factory)
    async with verify_uow:
        m = await verify_uow.merchants.get_by_name("Zara India")
        assert m is not None
        assert m.id == merchant_id

        p = await verify_uow.products.get_by_source_id(merchant_id, "Z12345")
        assert p is not None
        assert p.title == "Linen Shirt"

        g = await verify_uow.canonical_garments.get_by_id(garment_id)
        assert g is not None
        assert g.category == "tops"

        o = await verify_uow.offers.get_by_merchant_and_product(merchant_id, "Z12345")
        assert o is not None
        assert o.price_minor == 299000
