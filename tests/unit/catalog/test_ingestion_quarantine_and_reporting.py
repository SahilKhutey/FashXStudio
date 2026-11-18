"""Unit tests for quarantine lifecycle, run reporting, and error isolation (ING-027, ING-032 to ING-035, ING-039)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import IngestRun
from database.models.catalog_sync import CatalogIngestionQuarantine
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.acquisition.quarantine import CatalogQuarantineService
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_ing_027_and_034_invalid_record_quarantined_valid_processed_partial_status(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-027 & ING-034: Invalid record in a batch is quarantined, valid records succeed, run status is PARTIAL."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    valid_item = SourceProduct(
        source_slug=source_slug,
        source_product_id="VALID-SKU-1",
        title="Valid Silk Blouse",
        category="tops",
        price_minor=199900,
        currency="INR",
        product_url="https://merchant.example.com/p/valid-1",
    )
    invalid_item = SourceProduct(
        source_slug=source_slug,
        source_product_id="INVALID-SKU-2",
        title="",  # Invalid empty title!
        category="tops",
        price_minor=199900,
        currency="INR",
        product_url="https://merchant.example.com/p/invalid-2",
    )
    unmapped_item = SourceProduct(
        source_slug=source_slug,
        source_product_id="UNMAPPED-SKU-3",
        title="Unknown Hardware Item",
        category="gardening",  # Unmapped category!
        price_minor=199900,
        currency="INR",
        product_url="https://merchant.example.com/p/unmapped-3",
    )

    batch = AcquisitionBatch(
        source_slug=source_slug, products=[valid_item, invalid_item, unmapped_item]
    )
    report = await pipeline.process_batch(batch, apply=True)

    assert report.total_products == 3
    assert report.inserted == 1
    assert report.quarantined == 2
    assert report.rejected == 2
    assert report.status == "PARTIAL"
    assert report.success is True

    # Check quarantine table
    async with session_factory() as session:
        quarantine_stmt = select(CatalogIngestionQuarantine).where(
            CatalogIngestionQuarantine.ingest_run_id == report.ingest_run_id
        )
        records = (await session.execute(quarantine_stmt)).scalars().all()
        assert len(records) == 2
        reasons = {r.reason_code for r in records}
        assert "invalid_title" in reasons
        assert "category_unmapped" in reasons


@pytest.mark.asyncio
async def test_ing_032_quarantine_upsert_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-032: Quarantining the exact same invalid record repeatedly updates last_seen_at without creating duplicates."""
    source_id = setup_authorized_source["source_id"]
    run_id = uuid4()

    async with session_factory() as session:
        # Create IngestRun dummy row for foreign key
        dummy_run = IngestRun(
            id=run_id,
            source_id=source_id,
            status="RUNNING",
            counts={},
        )
        session.add(dummy_run)
        await session.commit()

    async with session_factory() as session:
        svc = CatalogQuarantineService(session)
        q1 = await svc.quarantine_record(
            ingest_run_id=run_id,
            source_id=source_id,
            source_product_id="BAD-ID-1",
            reason_code="invalid_price",
            raw_record={"price": -100},
        )
        await session.commit()
        id1 = q1.id

    async with session_factory() as session:
        svc = CatalogQuarantineService(session)
        q2 = await svc.quarantine_record(
            ingest_run_id=run_id,
            source_id=source_id,
            source_product_id="BAD-ID-1",
            reason_code="invalid_price",
            raw_record={"price": -100},
        )
        await session.commit()
        id2 = q2.id

    assert id1 == id2

    async with session_factory() as session:
        stmt = select(CatalogIngestionQuarantine).where(
            CatalogIngestionQuarantine.source_id == source_id,
            CatalogIngestionQuarantine.source_product_id == "BAD-ID-1",
        )
        all_records = (await session.execute(stmt)).scalars().all()
        assert len(all_records) == 1


@pytest.mark.asyncio
async def test_ing_033_run_completion_accurate_counts_and_timestamps(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-033: IngestRun records accurate counts, durations, and timestamps upon completion."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="PERF-COUNT-1",
        title="Formal Blazer",
        category="outerwear",
        subcategory="blazer",
        price_minor=399900,
        currency="INR",
        product_url="https://merchant.example.com/p/blazer",
    )
    report = await pipeline.process_batch(
        AcquisitionBatch(source_slug=source_slug, products=[item]), apply=True
    )
    assert report.finished_at is not None
    assert report.finished_at >= report.started_at

    async with session_factory() as session:
        run = await session.get(IngestRun, report.ingest_run_id)
        assert run is not None
        assert run.status == "COMPLETED"
        assert run.counts["total"] == 1
        assert run.counts["inserted"] == 1
        assert run.counts["rejected"] == 0


@pytest.mark.asyncio
async def test_ing_035_all_records_rejected_status_is_rejected(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-035: When all records in a batch fail validation, run status is REJECTED and success is False."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    item1 = SourceProduct(
        source_slug=source_slug,
        source_product_id="",  # Missing ID!
        title="Shirt",
        category="tops",
        price_minor=1000,
    )
    item2 = SourceProduct(
        source_slug=source_slug,
        source_product_id="P2",
        title="Product 2",
        category="unmapped_cat",  # Unmapped!
        price_minor=1000,
    )
    report = await pipeline.process_batch(
        AcquisitionBatch(source_slug=source_slug, products=[item1, item2]), apply=True
    )
    assert report.status == "REJECTED"
    assert report.success is False
    assert report.rejected == 2
    assert report.inserted == 0


@pytest.mark.asyncio
async def test_ing_039_repeated_sync_no_false_mass_deletion(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-039: Repeated batch executions do not delete or deactivate products unexpectedly."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="MASS-CHECK-1",
        title="Denim Shorts",
        category="bottoms",
        subcategory="shorts",
        price_minor=99900,
        currency="INR",
        product_url="https://merchant.example.com/p/shorts",
    )
    batch = AcquisitionBatch(source_slug=source_slug, products=[item])
    await pipeline.process_batch(batch, apply=True)

    # Empty batch must not delete previously ingested products
    empty_batch = AcquisitionBatch(source_slug=source_slug, products=[])
    await pipeline.process_batch(empty_batch, apply=True)

    async with uow:
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "MASS-CHECK-1")
        assert prod is not None
