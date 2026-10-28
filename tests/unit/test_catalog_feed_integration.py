"""Integration tests for catalog feed candidate queries and source filtering."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_feed_candidates_exclude_unapproved_and_inactive_sources(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CatalogUnitOfWork(session_factory)
    async with uow:
        # 1. Cleared Source
        cleared_source = CatalogSource(
            slug="store-cleared",
            name="Cleared Store",
            kind="api",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        uow.sources.add(cleared_source)

        # 2. Unapproved Pending Source
        pending_source = CatalogSource(
            slug="store-pending",
            name="Pending Store",
            kind="api",
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy="mirror",
        )
        uow.sources.add(pending_source)

        merchant = Merchant(name="Demo Retailer", merchant_type="retailer")
        uow.merchants.add(merchant)
        await uow.flush()

        # Garment 1: Belongs to cleared source (SHOULD BE IN FEED)
        garment_cleared = CanonicalGarment(
            display_name="Cleared Feed Shirt",
            category="tops",
            price_minor=149900,
            active=True,
            in_stock=True,
        )
        uow.canonical_garments.add(garment_cleared)
        await uow.flush()

        prod_cleared = MerchantProduct(
            merchant_id=merchant.id,
            canonical_garment_id=garment_cleared.id,
            source_id=cleared_source.id,
            source_product_id="SKU-CLEARED-1",
            title="Cleared Feed Shirt",
            source_url="https://cleared.com/p1",
            status="active",
        )
        uow.merchant_products.add(prod_cleared)

        offer_cleared = MerchantOffer(
            garment_id=garment_cleared.id,
            merchant_id=merchant.id,
            source_product_id="SKU-CLEARED-1",
            url="https://cleared.com/p1",
            price_minor=149900,
            currency="INR",
            in_stock=True,
        )
        uow.offers.add(offer_cleared)

        # Garment 2: Belongs to pending unapproved source (MUST BE EXCLUDED)
        garment_pending = CanonicalGarment(
            display_name="Pending Unapproved Top",
            category="tops",
            price_minor=89900,
            active=True,
            in_stock=True,
        )
        uow.canonical_garments.add(garment_pending)
        await uow.flush()

        prod_pending = MerchantProduct(
            merchant_id=merchant.id,
            canonical_garment_id=garment_pending.id,
            source_id=pending_source.id,
            source_product_id="SKU-PENDING-1",
            title="Pending Unapproved Top",
            source_url="https://pending.com/p2",
            status="active",
        )
        uow.merchant_products.add(prod_pending)

        offer_pending = MerchantOffer(
            garment_id=garment_pending.id,
            merchant_id=merchant.id,
            source_product_id="SKU-PENDING-1",
            url="https://pending.com/p2",
            price_minor=89900,
            currency="INR",
            in_stock=True,
        )
        uow.offers.add(offer_pending)

        await uow.commit()

    # Query feed candidates
    async with uow:
        candidates = await uow.canonical_garments.list_feed_candidates(limit=50)
        candidate_ids = [c.id for c in candidates]

        # Invariant: Cleared garment is included, pending garment is strictly excluded
        assert garment_cleared.id in candidate_ids
        assert garment_pending.id not in candidate_ids
