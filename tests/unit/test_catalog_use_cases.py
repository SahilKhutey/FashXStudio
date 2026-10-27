from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError


@pytest.mark.asyncio
async def test_ingest_product_missing_merchant_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    use_case = IngestMerchantProductUseCase(uow)

    cmd = IngestProductCommand(
        merchant_id=uuid4(),
        source_id=uuid4(),
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

    # 1. Setup merchant and an explicitly cleared test source.
    async with uow:
        merchant = Merchant(
            name="MVP1 Test Merchant",
            merchant_type="retailer",
        )
        source = CatalogSource(
            slug=f"mvp1-test-{uuid4().hex}",
            name="MVP1 Test Source",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
            terms_url="https://example.test/test-terms",
            notes="Synthetic test fixture only; never use as production evidence.",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
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
        source_id=source_id,
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


@pytest.mark.asyncio
async def test_ingest_product_validation_rules(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    use_case = IngestMerchantProductUseCase(uow)

    # Malformed URL
    with pytest.raises(ValidationError, match="URL"):
        await use_case.execute(
            IngestProductCommand(
                merchant_id=uuid4(),
                source_id=uuid4(),
                source_product_id="SKU-ERR-2",
                title="Valid Title",
                source_url="ftp://invalid-scheme.com",
                category="tops",
                price_minor=1000,
            )
        )

    # Unknown category
    with pytest.raises(ValidationError, match="category"):
        await use_case.execute(
            IngestProductCommand(
                merchant_id=uuid4(),
                source_id=uuid4(),
                source_product_id="SKU-ERR-3",
                title="Valid Title",
                source_url="https://merchant.com/3",
                category="electronics",
                price_minor=1000,
            )
        )


@pytest.mark.asyncio
async def test_ingest_product_requires_registered_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=uuid4(),
        source_product_id="SKU-NO-SOURCE",
        title="Test Shirt",
        source_url="https://example.test/products/shirt",
        category="tops",
        price_minor=199900,
        source_id=None,
    )
    with pytest.raises(ValidationError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_ingest_product_rejects_unapproved_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(
            name="Pending Test Merchant",
            merchant_type="retailer",
        )
        source = CatalogSource(
            slug=f"mvp1-pending-{uuid4().hex}",
            name="Pending Test Source",
            kind="manual",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="SKU-PENDING",
        title="Pending Shirt",
        source_url="https://example.test/products/pending",
        category="tops",
        price_minor=199900,
    )
    with pytest.raises(ValidationError) as exc_info:
        await use_case.execute(cmd)
    assert "not cleared" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ingest_product_rejects_source_without_display_rights(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(
            name="No Display Rights Merchant",
            merchant_type="retailer",
        )
        source = CatalogSource(
            slug=f"mvp1-no-display-{uuid4().hex}",
            name="No Display Source",
            kind="manual",
            status="cleared",
            rights_display=False,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="SKU-NO-DISPLAY",
        title="No Display Shirt",
        source_url="https://example.test/products/no-display",
        category="tops",
        price_minor=199900,
    )
    with pytest.raises(ValidationError) as exc_info:
        await use_case.execute(cmd)
    assert "display rights" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ingest_product_cleared_source_with_tryon_disabled_sets_tryon_supported_false(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(
            name="Display Only Merchant",
            merchant_type="retailer",
        )
        source = CatalogSource(
            slug=f"mvp1-display-only-{uuid4().hex}",
            name="Display Only Source",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        uow.merchants.add(merchant)
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id
        source_id = source.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_id=source_id,
        source_product_id="SKU-DISP-ONLY",
        title="Display Only Shirt",
        source_url="https://example.test/products/disp-only",
        category="tops",
        price_minor=199900,
    )
    res = await use_case.execute(cmd)
    assert res.tryon_supported is False

    async with uow:
        garment = await uow.canonical_garments.get_by_id(res.canonical_garment_id)
        assert garment is not None
        assert garment.tryon_supported is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("source_product_id", " "),
        ("title", " "),
        ("category", " "),
        ("source_url", "http://example.test/product/1"),
        ("source_url", "not-a-url"),
        ("currency", "USD"),
    ],
)
def test_product_input_validation_rejects_invalid_values(
    field_name: str,
    value: str,
) -> None:
    from fashx.catalog.application.ingest_product import validate_product_input

    fields = {
        "source_product_id": "SKU-100",
        "title": "Test Shirt",
        "source_url": "https://example.test/products/100",
        "category": "tops",
        "price_minor": 199900,
        "currency": "INR",
    }
    fields[field_name] = value
    with pytest.raises(ValidationError):
        validate_product_input(**fields)
