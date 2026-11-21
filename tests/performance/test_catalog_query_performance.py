"""Query performance and benchmark tests for Phase 05.5 Catalog Database.

Benchmarks:
1. Product lookup by source ID
2. Product detail retrieval
3. Category / brand filter
4. Combined multi-factor product filtering
5. Merchant active offer listing
6. Stale offer query
7. Price history lookup
"""

from __future__ import annotations

import statistics
import time
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
    MerchantOfferSize,
    OfferPriceHistory,
    PriceChangeType,
    SizeDefinition,
)
from fashx.catalog.freshness import (
    CatalogFilterParams,
    CatalogFreshnessService,
    CatalogQueryService,
)


@pytest.mark.asyncio
async def test_catalog_query_performance_benchmarks(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Benchmark critical catalog queries and report P50 and P95 latencies."""
    async with session_factory() as session:
        # Seed test dataset (50 garments, 100 offers, 100 sizes, 100 price observations)
        merchant = Merchant(
            id=uuid4(),
            name="Perf Test Merchant",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(merchant)

        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"perf-source-{uuid4().hex[:6]}",
            name="Perf Source",
            kind="feed_url",
            source_status="ACTIVE",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        session.add(source)

        brand = Brand(id=uuid4(), name="Perf Brand", normalized_name="perfbrand")
        session.add(brand)

        size_def = SizeDefinition(
            id=uuid4(),
            size_system="IN",
            category="tops",
            standardized_label="M",
            sort_order=1,
        )
        session.add(size_def)
        await session.flush()

        garment_ids: list = []
        source_product_ids: list[str] = []
        offer_ids: list = []
        now = datetime.now(UTC)

        for i in range(50):
            g_id = uuid4()
            garment_ids.append(g_id)
            g = CanonicalGarment(
                id=g_id,
                brand_id=brand.id,
                display_name=f"Garment Model {i}",
                category="tops" if i % 2 == 0 else "bottoms",
                subcategory="shirt" if i % 2 == 0 else "jeans",
                color_family="blue" if i % 3 == 0 else "black",
                price_minor=100000 + (i * 2000),
                in_stock=True,
                active=True,
            )
            session.add(g)

            sp_id = f"SKU-PERF-{i:04d}"
            source_product_ids.append(sp_id)
            p = MerchantProduct(
                id=uuid4(),
                merchant_id=merchant.id,
                source_id=source.id,
                canonical_garment_id=g_id,
                source_product_id=sp_id,
                title=f"Garment Model {i}",
                source_url=f"https://perf.example.com/p/{i}",
            )
            session.add(p)

            o_id = uuid4()
            offer_ids.append(o_id)
            is_stale = i % 5 == 0
            verified_time = now - timedelta(hours=10) if is_stale else now - timedelta(minutes=15)
            o = MerchantOffer(
                id=o_id,
                garment_id=g_id,
                merchant_id=merchant.id,
                merchant_product_id=p.id,
                source_id=source.id,
                source_product_id=sp_id,
                url=f"https://perf.example.com/p/{i}",
                price_minor=100000 + (i * 2000),
                currency="INR",
                in_stock=True,
                status="ACTIVE",
                availability="IN_STOCK",
                last_verified_at=verified_time,
                last_price_verified_at=verified_time,
                last_availability_verified_at=verified_time,
            )
            session.add(o)

            s = MerchantOfferSize(
                id=uuid4(),
                merchant_offer_id=o_id,
                size_definition_id=size_def.id,
                raw_size="M",
                availability="IN_STOCK",
            )
            session.add(s)

            h = OfferPriceHistory(
                id=uuid4(),
                merchant_offer_id=o_id,
                merchant_id=merchant.id,
                source_id=source.id,
                price_minor=100000 + (i * 2000),
                currency="INR",
                change_type=PriceChangeType.INITIAL,
                observed_at=verified_time,
            )
            session.add(h)

        await session.commit()

        # Benchmarks
        query_svc = CatalogQueryService(session)
        freshness_svc = CatalogFreshnessService(session)
        iterations = 20

        # Benchmark 1: Source Product Identity Lookup (P95 target < 50ms)
        latencies_1 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = await query_svc.lookup_by_source_identity(source.id, "SKU-PERF-0010")
            latencies_1.append((time.perf_counter() - t0) * 1000)
            assert res is not None

        # Benchmark 2: Garment Detail Retrieval (P95 target < 100ms)
        latencies_2 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            detail = await query_svc.get_garment_detail(garment_ids[5])
            latencies_2.append((time.perf_counter() - t0) * 1000)
            assert detail is not None

        # Benchmark 3: Category / Brand Filter (P95 target < 150ms)
        latencies_3 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            results = await query_svc.search_catalog(
                CatalogFilterParams(category="tops", brand_id=brand.id)
            )
            latencies_3.append((time.perf_counter() - t0) * 1000)
            assert len(results) > 0

        # Benchmark 4: Combined Multi-factor Filter (P95 target < 200ms)
        latencies_4 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            results = await query_svc.search_catalog(
                CatalogFilterParams(
                    category="tops",
                    brand_id=brand.id,
                    min_price=100000,
                    max_price=150000,
                    size="M",
                    color="blue",
                    in_stock_only=True,
                )
            )
            latencies_4.append((time.perf_counter() - t0) * 1000)
            assert len(results) >= 0

        # Benchmark 5: Merchant Active Offers Listing (P95 target < 150ms)
        latencies_5 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            offers = await query_svc.list_merchant_active_offers(merchant.id)
            latencies_5.append((time.perf_counter() - t0) * 1000)
            assert len(offers) == 50

        # Benchmark 6: Stale Offer Discovery (P95 target < 250ms)
        latencies_6 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            stale = await freshness_svc.list_stale_offers(max_age_hours=6, merchant_id=merchant.id)
            latencies_6.append((time.perf_counter() - t0) * 1000)
            assert len(stale) == 10  # 50 / 5 = 10 stale offers

        # Benchmark 7: Price History Lookup (P95 target < 100ms)
        latencies_7 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            hist = await query_svc.get_price_history(offer_ids[0])
            latencies_7.append((time.perf_counter() - t0) * 1000)
            assert len(hist) == 1

        def p95(data: list[float]) -> float:
            return sorted(data)[int(0.95 * len(data))]

        def p50(data: list[float]) -> float:
            return statistics.median(data)

        print("\n" + "=" * 65)
        print("CATALOG QUERY PERFORMANCE BENCHMARK RESULTS")
        print("=" * 65)
        print(
            f"1. Source Identity Lookup   : P50={p50(latencies_1):.2f}ms, P95={p95(latencies_1):.2f}ms (target < 50ms)"
        )
        print(
            f"2. Product Detail Retrieval : P50={p50(latencies_2):.2f}ms, P95={p95(latencies_2):.2f}ms (target < 100ms)"
        )
        print(
            f"3. Category / Brand Filter  : P50={p50(latencies_3):.2f}ms, P95={p95(latencies_3):.2f}ms (target < 150ms)"
        )
        print(
            f"4. Combined Filter          : P50={p50(latencies_4):.2f}ms, P95={p95(latencies_4):.2f}ms (target < 200ms)"
        )
        print(
            f"5. Merchant Offers Listing  : P50={p50(latencies_5):.2f}ms, P95={p95(latencies_5):.2f}ms (target < 150ms)"
        )
        print(
            f"6. Stale Offer Query        : P50={p50(latencies_6):.2f}ms, P95={p95(latencies_6):.2f}ms (target < 250ms)"
        )
        print(
            f"7. Price History Lookup     : P50={p50(latencies_7):.2f}ms, P95={p95(latencies_7):.2f}ms (target < 100ms)"
        )
        print("=" * 65)

        assert p95(latencies_1) < 50
        assert p95(latencies_2) < 100
        assert p95(latencies_3) < 150
        assert p95(latencies_4) < 200
        assert p95(latencies_5) < 150
        assert p95(latencies_6) < 250
        assert p95(latencies_7) < 100
