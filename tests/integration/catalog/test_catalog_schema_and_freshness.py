"""Integration tests for catalog database schema, freshness, multi-factor filtering, and discovery."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_freshness import (
    FreshnessState,
    MerchantOfferSize,
    SizeDefinition,
)
from fashx.catalog.freshness import (
    CatalogFilterParams,
    CatalogFreshnessService,
    CatalogQueryService,
)


@pytest.mark.asyncio
async def test_integration_catalog_query_and_multifactor_filtering(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Test CatalogQueryService with category, brand, price range, color, size, and stock filters."""
    async with session_factory() as session:
        # 1. Setup Merchant and Source
        merchant = Merchant(
            id=uuid4(),
            name="Integration Retailer",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(merchant)

        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"int-source-{uuid4().hex[:6]}",
            name="Integration Feed",
            kind="feed_url",
            source_status="ACTIVE",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        session.add(source)

        # 2. Setup Brands
        b1 = Brand(id=uuid4(), name="Nike", normalized_name="nike")
        b2 = Brand(id=uuid4(), name="Adidas", normalized_name="adidas")
        session.add_all([b1, b2])

        # 3. Setup Size Definitions
        sz_m = SizeDefinition(
            id=uuid4(),
            size_system="IN",
            category="tops",
            standardized_label="M",
            sort_order=2,
        )
        sz_l = SizeDefinition(
            id=uuid4(),
            size_system="IN",
            category="tops",
            standardized_label="L",
            sort_order=3,
        )
        session.add_all([sz_m, sz_l])
        await session.flush()

        # 4. Setup Garments
        # Garment 1: Nike Black Shirt, Size M, Price 1500, In Stock
        g1 = CanonicalGarment(
            id=uuid4(),
            brand_id=b1.id,
            display_name="Nike Dri-FIT Running Tee",
            category="tops",
            subcategory="t-shirt",
            color_family="black",
            price_minor=150000,
            in_stock=True,
            active=True,
        )
        session.add(g1)
        await session.flush()

        p1 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=source.id,
            canonical_garment_id=g1.id,
            source_product_id="NIKE-TEE-01",
            title="Nike Dri-FIT Running Tee",
            source_url="https://merchant.com/nike-tee",
        )
        session.add(p1)
        await session.flush()

        o1 = MerchantOffer(
            id=uuid4(),
            garment_id=g1.id,
            merchant_id=merchant.id,
            merchant_product_id=p1.id,
            source_id=source.id,
            source_product_id="NIKE-TEE-01",
            url="https://merchant.com/nike-tee",
            price_minor=150000,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            availability="IN_STOCK",
        )
        session.add(o1)
        await session.flush()

        s1 = MerchantOfferSize(
            id=uuid4(),
            merchant_offer_id=o1.id,
            size_definition_id=sz_m.id,
            raw_size="M",
            availability="IN_STOCK",
        )
        session.add(s1)

        # Garment 2: Adidas Blue Shirt, Size L, Price 2500, In Stock
        g2 = CanonicalGarment(
            id=uuid4(),
            brand_id=b2.id,
            display_name="Adidas Trefoil Hoodie",
            category="tops",
            subcategory="hoodie",
            color_family="blue",
            price_minor=250000,
            in_stock=True,
            active=True,
        )
        session.add(g2)
        await session.flush()

        p2 = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=source.id,
            canonical_garment_id=g2.id,
            source_product_id="ADI-HOODIE-01",
            title="Adidas Trefoil Hoodie",
            source_url="https://merchant.com/adi-hoodie",
        )
        session.add(p2)
        await session.flush()

        o2 = MerchantOffer(
            id=uuid4(),
            garment_id=g2.id,
            merchant_id=merchant.id,
            merchant_product_id=p2.id,
            source_id=source.id,
            source_product_id="ADI-HOODIE-01",
            url="https://merchant.com/adi-hoodie",
            price_minor=250000,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            availability="IN_STOCK",
        )
        session.add(o2)
        await session.flush()

        s2 = MerchantOfferSize(
            id=uuid4(),
            merchant_offer_id=o2.id,
            size_definition_id=sz_l.id,
            raw_size="L",
            availability="IN_STOCK",
        )
        session.add(s2)
        await session.commit()

        # 5. Query execution using CatalogQueryService
        query_svc = CatalogQueryService(session)

        # Filter 1: Brand = Nike -> Only g1
        res1 = await query_svc.search_catalog(CatalogFilterParams(brand_id=b1.id))
        assert len(res1) == 1
        assert res1[0].id == g1.id

        # Filter 2: Price range ₹1000 - ₹2000 -> Only g1 (1500)
        res2 = await query_svc.search_catalog(
            CatalogFilterParams(min_price=100000, max_price=200000)
        )
        assert len(res2) == 1
        assert res2[0].id == g1.id

        # Filter 3: Color = blue -> Only g2
        res3 = await query_svc.search_catalog(CatalogFilterParams(color="blue"))
        assert len(res3) == 1
        assert res3[0].id == g2.id

        # Filter 4: Size = M -> Only g1
        res4 = await query_svc.search_catalog(CatalogFilterParams(size="M"))
        assert len(res4) == 1
        assert res4[0].id == g1.id

        # Filter 5: Combined: Category=tops, Price <= 3000 -> Both g1 and g2
        res5 = await query_svc.search_catalog(
            CatalogFilterParams(category="tops", max_price=300000)
        )
        assert len(res5) == 2


@pytest.mark.asyncio
async def test_integration_stale_offer_detection_and_freshness(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Test CatalogFreshnessService stale offer detection and evaluation."""
    async with session_factory() as session:
        freshness_svc = CatalogFreshnessService(session)
        now = datetime.now(UTC)

        merchant = Merchant(id=uuid4(), name="Stale Test Merchant", merchant_type="brand")
        session.add(merchant)

        g = CanonicalGarment(id=uuid4(), display_name="Item 1", category="tops")
        session.add(g)
        await session.flush()

        # Fresh offer (verified 10 minutes ago)
        fresh_offer = MerchantOffer(
            id=uuid4(),
            garment_id=g.id,
            merchant_id=merchant.id,
            source_product_id="SKU-FRESH",
            url="https://example.com/fresh",
            price_minor=100000,
            status="ACTIVE",
            in_stock=True,
            last_verified_at=now - timedelta(minutes=10),
            last_price_verified_at=now - timedelta(minutes=10),
            last_availability_verified_at=now - timedelta(minutes=10),
        )
        session.add(fresh_offer)

        # Stale offer (verified 12 hours ago; policy max age 6h)
        stale_offer = MerchantOffer(
            id=uuid4(),
            garment_id=g.id,
            merchant_id=merchant.id,
            source_product_id="SKU-STALE",
            url="https://example.com/stale",
            price_minor=100000,
            status="ACTIVE",
            in_stock=True,
            last_verified_at=now - timedelta(hours=12),
            last_price_verified_at=now - timedelta(hours=12),
            last_availability_verified_at=now - timedelta(hours=12),
        )
        session.add(stale_offer)
        await session.commit()

        # Evaluate freshness individually
        fresh_eval = freshness_svc.evaluate_offer_freshness(fresh_offer, now=now)
        assert fresh_eval["overall"] == FreshnessState.CURRENT

        stale_eval = freshness_svc.evaluate_offer_freshness(stale_offer, now=now)
        assert stale_eval["overall"] == FreshnessState.STALE

        # List stale offers across merchant
        stale_list = await freshness_svc.list_stale_offers(max_age_hours=6, merchant_id=merchant.id)
        assert len(stale_list) == 1
        assert stale_list[0].id == stale_offer.id
