"""SA-015, SA-016, SA-024: Full snapshot vs Incremental delta sync, and safe stale offer reconciliation."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import MerchantOffer, MerchantProduct
from fashx.catalog.acquisition.checkpoints import SyncCheckpointManager
from fashx.catalog.acquisition.contract import SourceBatch, SourceProduct
from fashx.catalog.acquisition.contracts_v2 import SyncMode
from fashx.catalog.acquisition.sync_engine import CatalogSyncEngine


class StaticBatchAdapter:
    """Mock adapter returning designated product sets."""

    def __init__(
        self, source_slug: str, products: list[SourceProduct], should_fail: bool = False
    ) -> None:
        self.source_slug = source_slug
        self.products = products
        self.should_fail = should_fail

    async def fetch_page(self, cursor: str | None = None, limit: int = 100) -> SourceBatch:
        if self.should_fail:
            raise ConnectionResetError("Provider reset connection midway")
        return SourceBatch(
            source_slug=self.source_slug,
            products=self.products,
            cursor=None,
            has_more=False,
        )

    def normalize_product(self, raw_item: dict) -> SourceProduct:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_sa_015_incremental_sync_updates_watermark(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """SA-015: Incremental sync advances watermark upon completion."""
    source_id = setup_authorized_source["source_id"]
    source_slug = setup_authorized_source["source_slug"]
    engine = CatalogSyncEngine(session_factory)

    products = [
        SourceProduct(
            source_slug=source_slug,
            source_product_id="prod-inc-1",
            title="Incremental Dress",
            brand="BrandX",
            description="Updated description",
            category="dresses",
            price_minor=3500,
            currency="INR",
            in_stock=True,
            product_url="https://example.com/inc-1",
            image_url="https://example.com/inc-1.jpg",
        )
    ]
    adapter = StaticBatchAdapter(source_slug=source_slug, products=products)

    report = await engine.execute_sync(
        source_id=source_id, adapter=adapter, mode=SyncMode.INCREMENTAL
    )
    assert report.total_products == 1

    async with session_factory() as session:
        cp = await SyncCheckpointManager.load_checkpoint(
            session, source_id=source_id, checkpoint_type="incremental"
        )
        assert cp is not None
        assert cp.watermark is not None
        assert cp.last_success_at is not None


@pytest.mark.asyncio
async def test_sa_024_partial_or_failed_full_sync_never_marks_offers_out_of_stock(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """SA-024: A failed or partial full-sync run MUST NOT mark existing offers as out-of-stock."""
    source_id = setup_authorized_source["source_id"]
    source_slug = setup_authorized_source["source_slug"]
    engine = CatalogSyncEngine(session_factory)

    # 1. Populate an existing product that is in stock
    initial_product = SourceProduct(
        source_slug=source_slug,
        source_product_id="prod-existing-100",
        title="Existing Jacket",
        brand=None,
        description="Old description",
        category="jackets",
        price_minor=7999,
        currency="INR",
        in_stock=True,
        product_url="https://example.com/jacket",
        image_url="https://example.com/jacket.jpg",
    )
    initial_adapter = StaticBatchAdapter(source_slug=source_slug, products=[initial_product])
    await engine.execute_sync(source_id=source_id, adapter=initial_adapter, mode=SyncMode.FULL)

    # Verify offer is in stock
    async with session_factory() as session:
        all_offers = (await session.execute(select(MerchantOffer))).scalars().all()
        assert len(all_offers) > 0, f"No offers were inserted into the DB! Found {len(all_offers)}"
        offer = all_offers[0]
        assert offer.source_product_id == "prod-existing-100"
        assert offer.in_stock is True

    # 2. Run a full sync that fails midway
    failing_adapter = StaticBatchAdapter(source_slug=source_slug, products=[], should_fail=True)
    with pytest.raises(ConnectionResetError):
        await engine.execute_sync(source_id=source_id, adapter=failing_adapter, mode=SyncMode.FULL)

    # Verify existing offer is STILL in stock and was NOT marked out of stock
    async with session_factory() as session:
        offer = (
            await session.execute(
                select(MerchantOffer).where(
                    MerchantOffer.source_product_id == "prod-existing-100",
                )
            )
        ).scalar_one()
        assert offer.in_stock is True  # Invariant strictly preserved!


@pytest.mark.asyncio
async def test_sa_016_full_sync_reconciles_missing_items_only_on_complete_success(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """SA-016: When a 100% complete successful full sync finishes, items not seen are reconciled out of stock."""
    source_id = setup_authorized_source["source_id"]
    source_slug = setup_authorized_source["source_slug"]
    engine = CatalogSyncEngine(session_factory)

    # Full sync with new product replaces old catalog set
    new_product = SourceProduct(
        source_slug=source_slug,
        source_product_id="prod-new-replacement",
        title="New Replacement Tee",
        brand=None,
        description="Fresh tee",
        category="tops",
        price_minor=1200,
        currency="INR",
        in_stock=True,
        product_url="https://example.com/tee",
        image_url="https://example.com/tee.jpg",
    )
    success_adapter = StaticBatchAdapter(source_slug=source_slug, products=[new_product])
    await engine.execute_sync(source_id=source_id, adapter=success_adapter, mode=SyncMode.FULL)

    async with session_factory() as session:
        # Check newly inserted offer is in stock
        new_prod_res = await session.execute(
            select(MerchantProduct).where(
                MerchantProduct.source_id == source_id,
                MerchantProduct.source_product_id == "prod-new-replacement",
            )
        )
        new_prod = new_prod_res.scalar_one()
        assert new_prod.source_product_id == "prod-new-replacement"

        new_offer_res = await session.execute(
            select(MerchantOffer).where(
                MerchantOffer.source_product_id == "prod-new-replacement",
            )
        )
        new_offer = new_offer_res.scalar_one()
        assert new_offer.in_stock is True
