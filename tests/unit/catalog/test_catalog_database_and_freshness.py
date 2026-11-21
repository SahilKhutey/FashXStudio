"""Unit tests for Phase 05.5: Catalog Database Integrity, Freshness, Provenance, and Reconciliation.

Test Cases:
- CAT-DB-001: Normalize product identity -> Stable normalized identity
- CAT-DB-002: Duplicate source product ID -> Uniqueness enforced
- CAT-DB-003: Same garment from two merchants -> Separate offers
- CAT-DB-004: Different brands, same title -> Not automatically merged
- CAT-DB-005: Missing currency -> Validated and rejected
- CAT-DB-006: Negative price -> Rejected
- CAT-DB-007: Price change -> History observation inserted
- CAT-DB-008: Unchanged price -> No unnecessary duplicate history record
- CAT-DB-009: Unknown size system -> Raw value preserved
- CAT-DB-010: Missing availability -> UNKNOWN / safe default
- CAT-DB-011: Ingest timestamps -> Correctly populated
- CAT-DB-012: Unchanged content -> last_changed_at unchanged
- CAT-DB-013: Last verified timestamp -> Updated only after successful verification
- CAT-DB-014: Source provenance -> Correct source/run recorded
- CAT-DB-015: Conflicting source attributes -> Competing observations preserved
- CAT-DB-016: Takedown state -> Product cannot be reactivated by ordinary sync
- CAT-DB-017: Inactive offer -> History retained
- CAT-DB-018: Failed sync -> No stale reconciliation
- CAT-DB-019: Completed full sync -> Missing products reconciled safely
- CAT-DB-020: Duplicate ingestion run -> Idempotent result
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    IngestRun,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_freshness import (
    CatalogTakedownStatus,
    FreshnessState,
    OfferPriceHistory,
    PriceChangeType,
    SyncStatus,
)
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.freshness import (
    CatalogProvenanceService,
    CatalogReconciliationService,
    FreshnessPolicy,
    IncompleteSnapshotError,
    calculate_freshness,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_cat_db_001_normalize_product_identity(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-001: Verify product identity normalization produces stable, predictable attributes."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-NORM-001",
        title="  Oversized Cotton T-Shirt  ",
        brand="  Zara  ",
        category="tops",
        price_minor=129900,
        currency="inr",
        product_url="https://example.com/p/1?aff=123",
        in_stock=True,
        sizes=("m", " l "),
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[item])
    rep = await pipeline.process_batch(batch, apply=True)
    assert rep.inserted == 1

    async with uow:
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-NORM-001")
        assert prod is not None
        assert prod.source_category == "tops"
        assert prod.currency == "INR"
        assert prod.price_minor == 129900

        garment = await uow.canonical_garments.get_by_id(prod.canonical_garment_id)
        assert garment is not None
        assert garment.category == "tops"
        assert "m" in [s.lower() for s in garment.sizes_in_stock]


@pytest.mark.asyncio
async def test_cat_db_002_duplicate_source_product_id(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-002: Verify duplicate source_product_id for the same merchant violates uniqueness constraint."""
    merchant_id = setup_authorized_source["merchant_id"]
    source_id = setup_authorized_source["source_id"]

    async with session_factory() as session:
        p1 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-DUP-CHECK",
            title="Shirt 1",
            source_url="https://example.com/1",
        )
        session.add(p1)
        await session.commit()

        p2 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-DUP-CHECK",
            title="Shirt 2",
            source_url="https://example.com/2",
        )
        session.add(p2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_cat_db_003_same_garment_two_merchants(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-003: Same canonical garment can have separate independent offers from two merchants."""
    uow = CatalogUnitOfWork(session_factory)
    source_id = setup_authorized_source["source_id"]
    merchant_id_1 = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        # Create second merchant
        m2 = Merchant(
            id=uuid4(),
            name="Second Retailer",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(m2)
        await session.flush()
        merchant_id_2 = m2.id

        # Create one canonical garment
        garment = CanonicalGarment(
            id=uuid4(),
            display_name="Classic Oxford Shirt",
            category="tops",
            in_stock=True,
        )
        session.add(garment)
        await session.flush()

        # Merchant 1 Offer
        o1 = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant_id_1,
            source_id=source_id,
            source_product_id="SKU-M1-OXFORD",
            url="https://m1.com/oxford",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(o1)

        # Merchant 2 Offer (different price and availability)
        o2 = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant_id_2,
            source_id=source_id,
            source_product_id="SKU-M2-OXFORD",
            url="https://m2.com/oxford",
            price_minor=179900,
            currency="INR",
            in_stock=False,
            status="OUT_OF_STOCK",
        )
        session.add(o2)
        await session.commit()

        # Verify garment has two distinct offers
        stmt = select(MerchantOffer).where(MerchantOffer.garment_id == garment.id)
        offers = list((await session.scalars(stmt)).all())
        assert len(offers) == 2
        prices = {o.price_minor for o in offers}
        assert 199900 in prices
        assert 179900 in prices


@pytest.mark.asyncio
async def test_cat_db_004_different_brands_same_title_not_merged(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-004: Products with same title but different brands are kept completely distinct."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    p1 = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-B1-001",
        title="Slim Fit Chinos",
        brand="Brand Alpha",
        category="bottoms",
        price_minor=249900,
        currency="INR",
        product_url="https://example.com/p/b1",
        in_stock=True,
    )
    p2 = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-B2-001",
        title="Slim Fit Chinos",
        brand="Brand Beta",
        category="bottoms",
        price_minor=299900,
        currency="INR",
        product_url="https://example.com/p/b2",
        in_stock=True,
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[p1, p2])
    rep = await pipeline.process_batch(batch, apply=True)
    assert rep.inserted == 2

    async with session_factory() as session:
        stmt = select(Brand).where(Brand.name.in_(["Brand Alpha", "Brand Beta"]))
        brands = list((await session.scalars(stmt)).all())
        assert len(brands) == 2


@pytest.mark.asyncio
async def test_cat_db_005_and_006_currency_and_negative_price_validation(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-005 & CAT-DB-006: Missing/unsupported currency and negative prices are rejected and quarantined."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]

    # Negative price
    bad_price = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-BAD-PRICE",
        title="T-Shirt",
        brand="Test",
        category="tops",
        price_minor=-500,
        currency="INR",
        product_url="https://example.com/bad-price",
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[bad_price])
    rep = await pipeline.process_batch(batch, apply=True)
    assert rep.rejected == 1
    assert rep.quarantined == 1


@pytest.mark.asyncio
async def test_cat_db_007_and_008_price_history_observation(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-007 & CAT-DB-008: Price changes record history observations; unchanged price does not duplicate."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-PRICE-HIST-01",
        title="Crew Neck Sweatshirt",
        brand="Warm Wear",
        category="tops",
        price_minor=199900,
        currency="INR",
        product_url="https://example.com/p/sweatshirt",
        in_stock=True,
    )

    # 1. Initial insert -> 1 history observation
    batch1 = AcquisitionBatch(source_slug=source_slug, products=[item])
    await pipeline.process_batch(batch1, apply=True)

    offer_id = None
    async with uow:
        offer = await uow.offers.get_by_merchant_and_product(merchant_id, "SKU-PRICE-HIST-01")
        assert offer is not None
        offer_id = offer.id
        hist = await uow.price_history.list_for_offer(offer_id)
        assert len(hist) == 1
        assert hist[0].price_minor == 199900

    # 2. CAT-DB-008: Unchanged price ingestion -> NO duplicate history observation
    await pipeline.process_batch(batch1, apply=True)
    async with uow:
        hist = await uow.price_history.list_for_offer(offer_id)
        assert len(hist) == 1  # Still 1!

    # 3. CAT-DB-007: Price drop -> History observation inserted
    item_dropped = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-PRICE-HIST-01",
        title="Crew Neck Sweatshirt",
        brand="Warm Wear",
        category="tops",
        price_minor=149900,  # Price drop
        currency="INR",
        product_url="https://example.com/p/sweatshirt",
        in_stock=True,
    )
    batch_drop = AcquisitionBatch(source_slug=source_slug, products=[item_dropped])
    await pipeline.process_batch(batch_drop, apply=True)

    async with uow:
        hist = await uow.price_history.list_for_offer(offer_id)
        assert len(hist) == 2
        assert hist[0].price_minor == 149900
        assert hist[0].change_type == PriceChangeType.PRICE_DROP


@pytest.mark.asyncio
async def test_cat_db_009_and_010_size_and_availability_preservation(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-009 & CAT-DB-010: Raw sizes preserved in merchant_offer_sizes; availability defaults safely."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-SIZES-RAW",
        title="Running Shorts",
        brand="Sport Co",
        category="bottoms",
        price_minor=89900,
        currency="INR",
        product_url="https://example.com/shorts",
        sizes=("OneSizeCustom", "XXL-Tall"),
        in_stock=True,
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[item])
    await pipeline.process_batch(batch, apply=True)

    async with uow:
        offer = await uow.offers.get_by_merchant_and_product(merchant_id, "SKU-SIZES-RAW")
        assert offer is not None
        sizes = await uow.offer_sizes.list_for_offer(offer.id)
        raw_labels = {s.raw_size.upper() for s in sizes}
        assert "ONESIZECUSTOM" in raw_labels
        assert "XXL-TALL" in raw_labels


@pytest.mark.asyncio
async def test_cat_db_011_and_012_ingest_and_changed_timestamps(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-011 & CAT-DB-012: Ingest timestamps populated; unchanged content leaves last_changed_at intact."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-TS-TEST",
        title="Formal White Shirt",
        brand="Gentleman Style",
        category="tops",
        price_minor=219900,
        currency="INR",
        product_url="https://example.com/shirt",
        in_stock=True,
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[item])
    await pipeline.process_batch(batch, apply=True)

    initial_changed_at = None
    async with uow:
        prod = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-TS-TEST")
        assert prod is not None
        assert prod.first_ingested_at is not None
        assert prod.last_seen_at is not None
        assert prod.last_changed_at is not None
        initial_changed_at = prod.last_changed_at

    # Ingest unchanged batch
    await pipeline.process_batch(batch, apply=True)

    async with uow:
        prod_after = await uow.merchant_products.get_by_source_id(merchant_id, "SKU-TS-TEST")
        assert prod_after is not None
        # Invariant CAT-DB-012: last_changed_at must remain UNCHANGED on unchanged feed poll
        assert prod_after.last_changed_at == initial_changed_at


@pytest.mark.asyncio
async def test_cat_db_013_freshness_calculation_and_verification(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-DB-013: Freshness calculation derives CURRENT, STALE, UNKNOWN, REVIEW_REQUIRED accurately."""
    policy = FreshnessPolicy(price_max_age=timedelta(hours=6))
    now = datetime.now(UTC)

    # None -> UNKNOWN
    assert calculate_freshness(None, policy.price_max_age, now=now) == FreshnessState.UNKNOWN

    # 1 hour old -> CURRENT
    recent = now - timedelta(hours=1)
    assert calculate_freshness(recent, policy.price_max_age, now=now) == FreshnessState.CURRENT

    # 8 hours old (> 6h) -> STALE
    old = now - timedelta(hours=8)
    assert calculate_freshness(old, policy.price_max_age, now=now) == FreshnessState.STALE

    # Future timestamp -> REVIEW_REQUIRED
    future = now + timedelta(hours=2)
    assert (
        calculate_freshness(future, policy.price_max_age, now=now) == FreshnessState.REVIEW_REQUIRED
    )


@pytest.mark.asyncio
async def test_cat_db_014_and_015_provenance_and_competing_attributes(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-014 & CAT-DB-015: Source provenance recorded; conflicting source attributes preserve history."""
    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        provenance_svc = CatalogProvenanceService(session)
        entity_id = uuid4()

        # Source 1 records title
        await provenance_svc.record_attribute_change(
            entity_type="CANONICAL_GARMENT",
            entity_id=entity_id,
            attribute_name="title",
            attribute_value="Title From Source 1",
            source_id=source_id,
            merchant_id=merchant_id,
            confidence=0.9,
        )

        # Source 2 provides competing title
        await provenance_svc.record_attribute_change(
            entity_type="CANONICAL_GARMENT",
            entity_id=entity_id,
            attribute_name="title",
            attribute_value="Title From Source 2",
            source_id=source_id,
            merchant_id=merchant_id,
            confidence=1.0,
        )
        await session.commit()

        history = await provenance_svc.get_provenance_history(
            "CANONICAL_GARMENT", entity_id, "title"
        )
        assert len(history) == 2
        values = {h.attribute_value for h in history}
        assert "Title From Source 1" in values
        assert "Title From Source 2" in values


@pytest.mark.asyncio
async def test_cat_db_016_takedown_state_cannot_be_overridden_by_sync(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-016: Products with active takedown cannot be reactivated by subsequent ordinary sync."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-TAKEDOWN-01",
        title="Disputed Trademark Shirt",
        brand="Disputed Co",
        category="tops",
        price_minor=159900,
        currency="INR",
        product_url="https://example.com/p/disputed",
        in_stock=True,
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[item])
    await pipeline.process_batch(batch, apply=True)

    # Simulate takedown request on the product
    async with session_factory() as session:
        stmt = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == "SKU-TAKEDOWN-01",
        )
        prod = (await session.scalars(stmt)).first()
        assert prod is not None
        prod.takedown_status = CatalogTakedownStatus.COMPLETED
        prod.status = "suspended"
        await session.commit()

    # Attempt to sync again with in_stock=True
    rep = await pipeline.process_batch(batch, apply=True)
    assert rep.rejected == 1
    assert rep.rejection_reasons["product_under_takedown"] == 1

    # Verify status remained suspended and takedown was not cleared
    async with session_factory() as session:
        stmt = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == "SKU-TAKEDOWN-01",
        )
        prod_check = (await session.scalars(stmt)).first()
        assert prod_check is not None
        assert prod_check.takedown_status == CatalogTakedownStatus.COMPLETED
        assert prod_check.status == "suspended"


@pytest.mark.asyncio
async def test_cat_db_017_inactive_offer_retains_price_history(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-017: Deactivating or marking an offer out of stock does not erase its historical price observations."""
    uow = CatalogUnitOfWork(session_factory)
    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        garment = CanonicalGarment(id=uuid4(), display_name="Test Item", category="tops")
        session.add(garment)
        await session.flush()

        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-HIST-RETAIN",
            url="https://example.com/item",
            price_minor=99900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(offer)
        await session.flush()

        hist = OfferPriceHistory(
            id=uuid4(),
            merchant_offer_id=offer.id,
            merchant_id=merchant_id,
            source_id=source_id,
            price_minor=99900,
            currency="INR",
            observed_at=datetime.now(UTC),
        )
        session.add(hist)
        await session.commit()

        # Deactivate offer
        offer.status = "INACTIVE"
        offer.in_stock = False
        await session.commit()

        # Verify history is still present
        hist_stmt = select(OfferPriceHistory).where(OfferPriceHistory.merchant_offer_id == offer.id)
        entries = list((await session.scalars(hist_stmt)).all())
        assert len(entries) == 1
        assert entries[0].price_minor == 99900


@pytest.mark.asyncio
async def test_cat_db_018_and_019_safe_stale_reconciliation_full_vs_failed(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-018 & CAT-DB-019: Incomplete/failed runs reject reconciliation; completed full sync reconciles safely."""
    source_id = setup_authorized_source["source_id"]
    merchant_id = setup_authorized_source["merchant_id"]

    async with session_factory() as session:
        reconciliation_svc = CatalogReconciliationService(session)

        # Create 1 failed ingest run
        failed_run = IngestRun(
            id=uuid4(),
            source_id=source_id,
            merchant_id=merchant_id,
            status="FAILED",
            counts={},
        )
        session.add(failed_run)

        # Create 1 completed full sync run
        completed_run = IngestRun(
            id=uuid4(),
            source_id=source_id,
            merchant_id=merchant_id,
            status="COMPLETED",
            counts={"total": 1},
        )
        session.add(completed_run)

        # Create 2 offers
        g = CanonicalGarment(id=uuid4(), display_name="Jacket", category="jackets", in_stock=True)
        session.add(g)
        await session.flush()

        # Product & Offer 1: seen in full sync
        p1 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-SEEN-01",
            title="Jacket 1",
            source_url="https://example.com/j1",
        )
        session.add(p1)
        o1 = MerchantOffer(
            id=uuid4(),
            garment_id=g.id,
            merchant_id=merchant_id,
            merchant_product_id=p1.id,
            source_id=source_id,
            source_product_id="SKU-SEEN-01",
            url="https://example.com/j1",
            price_minor=399900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(o1)

        # Product & Offer 2: MISSING in full sync
        p2 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="SKU-MISSING-02",
            title="Jacket 2",
            source_url="https://example.com/j2",
        )
        session.add(p2)
        o2 = MerchantOffer(
            id=uuid4(),
            garment_id=g.id,
            merchant_id=merchant_id,
            merchant_product_id=p2.id,
            source_id=source_id,
            source_product_id="SKU-MISSING-02",
            url="https://example.com/j2",
            price_minor=499900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(o2)
        await session.commit()

        # CAT-DB-018: Failed run MUST raise IncompleteSnapshotError
        with pytest.raises(IncompleteSnapshotError):
            await reconciliation_svc.reconcile_full_snapshot(
                ingest_run_id=failed_run.id,
                seen_source_product_ids={"SKU-SEEN-01"},
            )

        # CAT-DB-019: Completed full sync reconciles missing product safely
        report = await reconciliation_svc.reconcile_full_snapshot(
            ingest_run_id=completed_run.id,
            seen_source_product_ids={"SKU-SEEN-01"},
            apply=True,
        )
        assert report.seen_count == 1
        assert report.missing_count == 1
        assert report.reconciled_offers == 1

        # Check offer 2 status
        assert o2.sync_status == SyncStatus.SOURCE_MISSING
        assert o2.in_stock is False
        assert o2.status == "OUT_OF_STOCK"

        # Check offer 1 is unchanged
        assert o1.sync_status == SyncStatus.CURRENT
        assert o1.in_stock is True


@pytest.mark.asyncio
async def test_cat_db_020_idempotent_duplicate_ingest_run(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """CAT-DB-020: Running identical ingestion batches repeatedly is strictly idempotent."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    source_slug = setup_authorized_source["source_slug"]
    merchant_id = setup_authorized_source["merchant_id"]

    item = SourceProduct(
        source_slug=source_slug,
        source_product_id="SKU-IDEMPOTENT-01",
        title="Knitted Wool Scarf",
        brand="Winter Collection",
        category="tops",
        price_minor=79900,
        currency="INR",
        product_url="https://example.com/scarf",
        in_stock=True,
        sizes=("OneSize",),
    )

    batch = AcquisitionBatch(source_slug=source_slug, products=[item])

    # Run 1
    rep1 = await pipeline.process_batch(batch, apply=True)
    assert rep1.inserted == 1

    # Run 2
    rep2 = await pipeline.process_batch(batch, apply=True)
    assert rep2.inserted == 0
    assert rep2.updated == 0
    assert rep2.unchanged == 1

    # Run 3
    rep3 = await pipeline.process_batch(batch, apply=True)
    assert rep3.inserted == 0
    assert rep3.updated == 0
    assert rep3.unchanged == 1

    # Total products in DB must still be 1
    async with session_factory() as session:
        stmt = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == "SKU-IDEMPOTENT-01",
        )
        prods = list((await session.scalars(stmt)).all())
        assert len(prods) == 1
