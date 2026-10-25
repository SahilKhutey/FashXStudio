"""Unit and database tests for the AcquisitionPipeline."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_pipeline_rejects_unregistered_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug="unregistered-store",
        products=[
            SourceProduct(
                source_slug="unregistered-store",
                source_product_id="SKU-1",
                title="Shirt",
                category="tops",
                price_minor=99900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.total_products == 1
    assert report.rejected == 1
    assert any("unregistered_source" in k for k in report.rejection_reasons)


@pytest.mark.asyncio
async def test_pipeline_rejects_unapproved_source_by_default(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        source = CatalogSource(
            slug="pending-store",
            name="Pending Store",
            kind="api",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()

    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug="pending-store",
        products=[
            SourceProduct(
                source_slug="pending-store",
                source_product_id="SKU-2",
                title="Trousers",
                category="bottoms",
                price_minor=199900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.rejected == 1
    assert any("source_not_cleared" in k for k in report.rejection_reasons)


@pytest.mark.asyncio
async def test_pipeline_idempotent_ingestion_and_change_tracking(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        source = CatalogSource(
            slug="cleared-store",
            name="Cleared Retailer",
            kind="api",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()

    pipeline = AcquisitionPipeline(uow)
    item = SourceProduct(
        source_slug="cleared-store",
        source_product_id="SKU-100",
        title="Linen Casual Shirt",
        brand="Retail Brand",
        category="tops",
        subcategory="shirt",
        price_minor=149900,
        currency="INR",
        product_url="https://cleared-store.example.com/p/100",
        image_url="https://images.example.com/p/100.jpg",
        in_stock=True,
        sizes=("M", "L", "XL"),
        image_rights="partner_authorized",
        tryon_rights=True,
    )

    # 1. First ingestion (INSERT)
    batch1 = AcquisitionBatch(source_slug="cleared-store", products=[item])
    report1 = await pipeline.process_batch(batch1, apply=True)
    assert report1.success is True
    assert report1.total_products == 1
    assert report1.inserted == 1
    assert report1.updated == 0
    assert report1.unchanged == 0
    assert report1.rejected == 0
    assert report1.ingest_run_id is not None

    merchant_id = None
    # Verify records created in database
    async with uow:
        merchants = await uow.merchants.list(limit=10)
        assert len(merchants) > 0
        merchant_id = merchants[0].id
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-100")
        assert prod is not None
        assert prod.title == "Linen Casual Shirt"
        assert prod.canonical_garment_id is not None

        garment = await uow.canonical_garments.get_by_id(prod.canonical_garment_id)
        assert garment is not None
        assert garment.price_minor == 149900
        assert garment.tryon_supported is True

        offers = await uow.offers.list_for_garment(garment.id)
        assert len(offers) == 1
        assert offers[0].price_minor == 149900
        assert offers[0].in_stock is True

        images = await uow.images.list_for_garment(garment.id)
        assert len(images) == 1

        # Verify IngestRun was recorded
        run = await uow.ingest_runs.get_by_id(report1.ingest_run_id)
        assert run is not None
        assert run.status == "ok"
        assert run.counts["inserted"] == 1

    # 2. Repeated ingestion with no changes (UNCHANGED)
    report2 = await pipeline.process_batch(batch1, apply=True)
    assert report2.inserted == 0
    assert report2.updated == 0
    assert report2.unchanged == 1
    assert report2.rejected == 0

    # 3. Subsequent ingestion with price & stock change (UPDATE)
    updated_item = SourceProduct(
        source_slug="cleared-store",
        source_product_id="SKU-100",
        title="Linen Casual Shirt",
        brand="Retail Brand",
        category="tops",
        subcategory="shirt",
        price_minor=129900,  # Price drop!
        currency="INR",
        product_url="https://cleared-store.example.com/p/100",
        image_url="https://images.example.com/p/100.jpg",
        in_stock=False,  # Out of stock!
        sizes=("M", "L"),
        image_rights="partner_authorized",
        tryon_rights=True,
    )
    batch3 = AcquisitionBatch(source_slug="cleared-store", products=[updated_item])
    report3 = await pipeline.process_batch(batch3, apply=True)
    assert report3.inserted == 0
    assert report3.updated == 1
    assert report3.unchanged == 0
    assert report3.rejected == 0

    # Verify changes reflected in DB
    async with uow:
        assert merchant_id is not None
        updated_prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-100")
        assert updated_prod is not None
        assert updated_prod.canonical_garment_id is not None
        garment = await uow.canonical_garments.get_by_id(updated_prod.canonical_garment_id)
        assert garment is not None
        assert garment.price_minor == 129900
        assert garment.in_stock is False
        assert garment.sizes_in_stock == ["M", "L"]

        offers = await uow.offers.list_for_garment(garment.id)
        assert offers[0].price_minor == 129900
        assert offers[0].in_stock is False
