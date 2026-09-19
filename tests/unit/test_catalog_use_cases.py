from uuid import uuid4

import pytest
from api.app.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from api.app.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import EntityNotFoundError, ValidationError
from database.models.catalog import Merchant
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_ingest_product_missing_merchant_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    use_case = IngestMerchantProductUseCase(uow)

    cmd = IngestProductCommand(
        merchant_id=uuid4(),
        source_product_id="SKU-100",
        title="Classic Oxford Shirt",
        source_url="https://merchant.example.com/items/100",
        category="shirts",
        price_minor=249900,
    )

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_ingest_product_negative_price_raises_validation_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    use_case = IngestMerchantProductUseCase(uow)

    cmd = IngestProductCommand(
        merchant_id=uuid4(),
        source_product_id="SKU-100",
        title="Classic Oxford Shirt",
        source_url="https://merchant.example.com/items/100",
        category="shirts",
        price_minor=-100,
    )

    with pytest.raises(ValidationError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_ingest_product_success_and_idempotent_update(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)

    # 1. Setup merchant
    async with uow:
        merchant = Merchant(name="Myntra Direct", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="MYN-44910",
        title="Slim Fit Linen Shirt",
        source_url="https://myntra.com/shirts/44910",
        category="tops",
        subcategory="casual_shirts",
        price_minor=189900,
    )

    # 2. Ingest
    res1 = await use_case.execute(cmd)
    assert res1.title == "Slim Fit Linen Shirt"
    assert res1.category == "tops"
    assert res1.price_minor == 189900

    # 3. Ingest update with new price
    cmd_update = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="MYN-44910",
        title="Slim Fit Linen Shirt - Updated",
        source_url="https://myntra.com/shirts/44910",
        category="tops",
        subcategory="casual_shirts",
        price_minor=159900,
    )
    res2 = await use_case.execute(cmd_update)

    # Garment ID should be preserved
    assert res2.canonical_garment_id == res1.canonical_garment_id
    assert res2.merchant_product_id == res1.merchant_product_id
    assert res2.offer_id == res1.offer_id
    assert res2.price_minor == 159900
    assert res2.title == "Slim Fit Linen Shirt - Updated"
