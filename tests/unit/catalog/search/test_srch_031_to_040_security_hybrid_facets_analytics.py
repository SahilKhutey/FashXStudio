from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from database.models.catalog import MerchantProduct
from database.models.catalog_image import CatalogImageTakedown, ImageTakedownStatus
from database.models.catalog_search import (
    ProductSearchDocumentRecord,
    ProductSearchEventRecord,
)
from fashx.catalog.search.candidate_merger import merge_candidates_rrf
from fashx.catalog.search.contracts import (
    ProductSearchRequest,
)
from fashx.catalog.search.facets import compute_facets
from fashx.catalog.search.ranking import apply_business_ranking
from fashx.catalog.search.search_service import FashionSearchService


def test_srch_031_cross_tenant_isolation(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-031: Results maintain merchant source boundaries without leaking unpermitted data."""
    service = FashionSearchService()
    req = ProductSearchRequest(limit=10)
    res = service.search(search_sync_session, req)

    for item in res.items:
        mp = search_sync_session.get(MerchantProduct, item.merchant_product_id)
        assert mp is not None
        # Every item matches an authorized merchant product in the catalog
        assert mp.merchant_id in [setup_search_catalog["merch_a"].id, setup_search_catalog["merch_b"].id]


def test_srch_032_hybrid_rrf_merging() -> None:
    """Verify SRCH-032: Reciprocal Rank Fusion ranks items appearing across multiple streams higher."""
    id_shared = uuid4()
    id_stream1_only = uuid4()
    id_stream2_only = uuid4()

    stream_data = {
        "keyword": [(id_shared, 1.0), (id_stream1_only, 0.9)],
        "semantic": [(id_shared, 0.95), (id_stream2_only, 0.85)],
    }

    merged = merge_candidates_rrf(stream_data, k=60)
    # Item appearing in both streams should rank first
    assert merged[0][0] == id_shared
    assert merged[0][1] > merged[1][1]


def test_srch_033_search_document_update(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-033: Updating product search document immediately reflects in search."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]

    doc1 = session.query(ProductSearchDocumentRecord).filter_by(merchant_product_id=mp1.id).first()
    assert doc1 is not None

    # Update search document with unique token
    unique_term = "aerocool_breathable_fabric"
    doc1.search_document = f"{doc1.search_document} {unique_term}"
    session.commit()

    service = FashionSearchService()
    req = ProductSearchRequest(q=unique_term)
    res = service.search(session, req)

    assert res.total >= 1
    assert any(it.merchant_product_id == mp1.id for it in res.items)


def test_srch_034_search_cache_invalidation(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-034: Takedown dynamically purges item from an active search session pagination."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]

    service = FashionSearchService()
    # Initial search creating session
    req1 = ProductSearchRequest(limit=1)
    res1 = service.search(session, req1)
    assert res1.next_cursor is not None

    # Takedown occurs after search session creation
    takedown = CatalogImageTakedown(
        id=uuid4(),
        source_id=cat["source_a"].id,
        merchant_id=cat["merch_a"].id,
        scope_type="source",
        scope_target=str(cat["source_a"].id),
        reason_code="DMCA",
        status=ImageTakedownStatus.PROCESSING.value,
    )
    session.add(takedown)
    session.commit()

    # Next cursor request re-checks takedown dynamically
    req2 = ProductSearchRequest(cursor=res1.next_cursor, limit=10)
    res2 = service.search(session, req2)

    # All items from source_a should be excluded
    assert not any(it.merchant_product_id == mp1.id for it in res2.items)

    session.delete(takedown)
    session.commit()


def test_srch_035_facet_counts_reflection(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-035: Facet distributions reflect matching product candidates."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]
    mp3 = cat["mp3"]

    facets = compute_facets(session, [mp1.id, mp3.id])

    # Both mp1 and mp3 belong to brand Roadster
    brands = {b["name"]: b["count"] for b in facets["brands"]}
    assert brands.get("Roadster") == 2
    assert "FabIndia" not in brands


def test_srch_036_search_analytics_event_recording(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-036: Search events (clicks, impressions) are recorded into audit records."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]
    user_id = uuid4()

    event = ProductSearchEventRecord(
        id=uuid4(),
        session_id=None,
        user_id=user_id,
        event_type="product_click",
        merchant_product_id=mp1.id,
        rank_position=1,
        metadata_json={"time_spent_ms": 3200},
    )
    session.add(event)
    session.commit()

    saved = session.get(ProductSearchEventRecord, event.id)
    assert saved is not None
    assert saved.event_type == "product_click"
    assert saved.merchant_product_id == mp1.id
    assert saved.rank_position == 1


def test_srch_037_filter_combinations_and_or(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-037: Multi-attribute composite filter intersection."""
    service = FashionSearchService()
    cat = setup_search_catalog

    # Match Category=Tops + Brand=Roadster + Price < 600 (should match mp3 ₹499, exclude mp1 ₹899)
    req = ProductSearchRequest(
        category_id=cat["cat_tops"].id,
        brand_id=cat["brand_roadster"].id,
        max_price=Decimal("600"),
    )
    res = service.search(search_sync_session, req)

    assert res.total == 1
    assert res.items[0].merchant_product_id == cat["mp3"].id


def test_srch_038_multi_merchant_listing_segregation(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-038: Multiple merchant offerings for same canonical garment are distinct cards."""
    cat = setup_search_catalog
    service = FashionSearchService()

    # mp1 and mp3 share canonical garment g1, but have different merchant product IDs
    req = ProductSearchRequest(brand_id=cat["brand_roadster"].id)
    res = service.search(search_sync_session, req)

    mp_ids = [it.merchant_product_id for it in res.items]
    assert cat["mp1"].id in mp_ids
    assert cat["mp3"].id in mp_ids
    # Separate distinct cards
    assert len(set(mp_ids)) == len(mp_ids)


def test_srch_039_low_confidence_attributes_not_facts(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-039: Low-confidence attributes (< 0.70) are not treated as verified."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]

    doc1 = session.query(ProductSearchDocumentRecord).filter_by(merchant_product_id=mp1.id).first()
    assert doc1 is not None

    # Degrade confidence
    doc1.indexed_attributes_json = {
        "color": "black",
        "confidence": 0.45,  # Low confidence inference
    }
    session.commit()

    # Low confidence does not receive verified business boost
    candidates = [(mp1.id, 1.0)]
    boosted = apply_business_ranking(
        candidates=candidates,
        query_text=None,
        search_docs={mp1.id: doc1},
    )
    # Score remains unchanged (no boost)
    assert boosted[0][1] == 1.0


def test_srch_040_query_injection_safety(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-040: Malicious SQL injection payloads are handled safely without DB errors."""
    service = FashionSearchService()

    payloads = [
        "'; DROP TABLE merchant_products; --",
        "' OR '1'='1",
        "UNION SELECT NULL, NULL, NULL --",
        "<script>alert('xss')</script>",
        "'; EXEC xp_cmdshell('dir'); --",
    ]

    for p in payloads:
        req = ProductSearchRequest(q=p)
        # Must execute cleanly without unhandled database or parsing exceptions
        res = service.search(search_sync_session, req)
        assert isinstance(res.total, int)
