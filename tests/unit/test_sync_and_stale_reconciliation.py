"""Unit and database tests for CatalogSyncService and stale offer reconciliation."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
)
from fashx.catalog.acquisition.adapters.partner_feed import PartnerFeedAdapter
from fashx.catalog.acquisition.contract import SourceProduct
from fashx.catalog.acquisition.registry import AdapterRegistry
from fashx.catalog.acquisition.sync_service import CatalogSyncService
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_sync_service_sync_source_and_failure_isolation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        # Pre-register cleared source
        source = CatalogSource(
            slug="store-alpha",
            name="Store Alpha",
            kind="api",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.sources.add(source)
        await uow.commit()

    registry = AdapterRegistry()
    adapter_alpha = PartnerFeedAdapter(
        feed_items=[
            SourceProduct(
                source_slug="store-alpha",
                source_product_id="A-101",
                title="Alpha Oxford Shirt",
                category="tops",
                price_minor=159900,
            )
        ]
    )
    # Patch slug to match registered source
    adapter_alpha.config.source_slug = "store-alpha"
    registry.register(adapter_alpha)

    # Register a broken second adapter to test failure isolation
    class BrokenAdapter:
        source_slug = "broken-store"

        async def fetch_batch(self, cursor=None, limit=100):
            raise RuntimeError("Fatal network error")

    registry.register(BrokenAdapter())  # type: ignore[arg-type]

    service = CatalogSyncService(session_factory=session_factory, registry=registry)

    # Sync all sources: failure in broken-store must not prevent store-alpha from succeeding!
    reports = await service.sync_all_sources(apply=True)
    assert len(reports) == 2
    assert reports["store-alpha"].success is True
    assert reports["store-alpha"].inserted == 1
    assert reports["broken-store"].success is False


@pytest.mark.asyncio
async def test_reconcile_stale_offers(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    now = datetime.now(UTC)
    stale_time = now - timedelta(hours=72)  # 3 days old

    async with uow:
        merchant = Merchant(name="Test Retailer", merchant_type="brand")
        uow.merchants.add(merchant)

        garment = CanonicalGarment(
            display_name="Stale Jeans",
            category="bottoms",
            price_minor=199900,
            in_stock=True,
        )
        uow.canonical_garments.add(garment)
        await uow.flush()

        # Stale offer (72 hours old)
        stale_offer = MerchantOffer(
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_product_id="SKU-STALE",
            url="https://example.com/stale",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            last_synced_at=stale_time,
        )
        uow.offers.add(stale_offer)
        await uow.commit()

    service = CatalogSyncService(session_factory=session_factory)

    # Reconcile with 48h threshold -> 72h offer must be marked out of stock
    reconciled_count = await service.reconcile_stale_offers(stale_threshold_hours=48, apply=True)
    assert reconciled_count == 1

    # Verify database state
    async with uow:
        updated_offer = await uow.offers.get_by_id(stale_offer.id)
        assert updated_offer is not None
        assert updated_offer.in_stock is False

        updated_garment = await uow.canonical_garments.get_by_id(garment.id)
        assert updated_garment is not None
        assert updated_garment.in_stock is False
