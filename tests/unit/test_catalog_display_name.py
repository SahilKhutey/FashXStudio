import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.application import IngestMerchantProductUseCase, IngestProductCommand
from fashx.catalog.repositories.catalog import CatalogRepository
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_ingest_product_sets_display_name_from_title(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Brand Direct", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="SKU-TITLE-1",
        title="Embroidered Festive Kurta",
        source_url="https://example.com/items/1",
        category="tops",
        subcategory="kurta",
        price_minor=249900,
    )
    res = await use_case.execute(cmd)
    garment = await uow.canonical_garments.get_by_id(res.canonical_garment_id)
    assert garment is not None
    assert garment.display_name == "Embroidered Festive Kurta"


@pytest.mark.asyncio
async def test_ingest_product_falls_back_to_subcategory_when_title_empty(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Brand Direct 2", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="SKU-TITLE-2",
        title="",
        source_url="https://example.com/items/2",
        category="tops",
        subcategory="casual_shirts",
        price_minor=189900,
    )
    res = await use_case.execute(cmd)
    garment = await uow.canonical_garments.get_by_id(res.canonical_garment_id)
    assert garment is not None
    assert garment.display_name == "casual_shirts"


@pytest.mark.asyncio
async def test_ingest_product_falls_back_to_category_when_title_and_subcat_empty(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        merchant = Merchant(name="Brand Direct 3", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()
        source = CatalogSource(
            slug=f"merchant-{merchant.id}",
            name=merchant.name,
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()
        merchant_id = merchant.id

    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=merchant_id,
        source_product_id="SKU-TITLE-3",
        title="",
        source_url="https://example.com/items/3",
        category="dresses",
        subcategory="",
        price_minor=299900,
    )
    res = await use_case.execute(cmd)
    garment = await uow.canonical_garments.get_by_id(res.canonical_garment_id)
    assert garment is not None
    assert garment.display_name == "dresses"


@pytest.mark.asyncio
async def test_catalog_repository_create_garment_sets_display_name_and_fallback(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repo = CatalogRepository(session)
        # 1. Explicit display_name
        g1 = await repo.create_garment(category="tops", subcategory="linen_shirt", display_name="My Linen Shirt")
        assert g1.display_name == "My Linen Shirt"

        # 2. Fallback to subcategory
        g2 = await repo.create_garment(category="tops", subcategory="linen_shirt")
        assert g2.display_name == "linen_shirt"

        # 3. Fallback to category
        g3 = await repo.create_garment(category="tops")
        assert g3.display_name == "tops"
