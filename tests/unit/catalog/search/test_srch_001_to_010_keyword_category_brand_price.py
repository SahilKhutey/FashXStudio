from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.orm import Session

from fashx.catalog.search.contracts import ProductSearchRequest
from fashx.catalog.search.search_service import FashionSearchService


def test_srch_001_keyword_exact_match(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-001: Exact keyword match returns relevant product."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="Men's Black Casual Shirt", limit=10)
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert any("Black Casual Shirt" in item.title for item in res.items)


def test_srch_002_keyword_partial_match(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-002: Partial keyword matches product title."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="kurta", limit=10)
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert any("Kurta" in item.title for item in res.items)


def test_srch_003_case_variation(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-003: Case variation yields identical result sets."""
    service = FashionSearchService()
    res_lower = service.search(search_sync_session, ProductSearchRequest(q="black shirt"))
    res_upper = service.search(search_sync_session, ProductSearchRequest(q="BLACK SHIRT"))

    assert res_lower.total == res_upper.total
    assert [it.merchant_product_id for it in res_lower.items] == [
        it.merchant_product_id for it in res_upper.items
    ]


def test_srch_004_empty_query(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-004: Empty query returns catalog browse results."""
    service = FashionSearchService()
    res = service.search(search_sync_session, ProductSearchRequest(q=None, limit=20))

    assert res.total >= 3
    assert len(res.items) >= 3


def test_srch_005_excessively_long_query() -> None:
    """Verify SRCH-005: Query exceeding 200 characters is rejected."""
    long_q = "cotton shirt " * 30  # ~390 chars
    with pytest.raises(ValueError):
        ProductSearchRequest(q=long_q)


def test_srch_006_category_filter(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-006: Category filter matches leaf taxonomy ID."""
    cat_kurta = setup_search_catalog["cat_kurta"]
    service = FashionSearchService()
    req = ProductSearchRequest(category_id=cat_kurta.id)
    res = service.search(search_sync_session, req)

    assert res.total == 1
    assert "Kurta" in res.items[0].title


def test_srch_007_parent_category_descendants(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-007: Selecting parent category includes descendant subcategory products."""
    cat_tops = setup_search_catalog["cat_tops"]
    service = FashionSearchService()
    req = ProductSearchRequest(category_id=cat_tops.id)
    res = service.search(search_sync_session, req)

    # cat_tops has child cat_tshirt containing mp1 (shirt) and mp3 (tee)
    assert res.total >= 2
    titles = [it.title for it in res.items]
    assert any("Black Casual Shirt" in t for t in titles)
    assert any("T-Shirt" in t for t in titles)


def test_srch_008_brand_filter(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-008: Brand filter restricts strictly to canonical brand."""
    brand_fabindia = setup_search_catalog["brand_fabindia"]
    service = FashionSearchService()
    req = ProductSearchRequest(brand_id=brand_fabindia.id)
    res = service.search(search_sync_session, req)

    assert res.total == 1
    assert res.items[0].brand.name == "FabIndia"


def test_srch_009_brand_alias(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-009: Brand search in keyword finds brand products."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="Roadster", limit=10)
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert all(it.brand.name == "Roadster" for it in res.items)


def test_srch_010_price_range(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-010: Price range filters active eligible offer prices."""
    service = FashionSearchService()
    # Filter between ₹400 and ₹900 (should match mp3 at ₹499 and mp1 at ₹899; exclude mp2 at ₹1499)
    req = ProductSearchRequest(min_price=Decimal("400.00"), max_price=Decimal("900.00"))
    res = service.search(search_sync_session, req)

    assert res.total == 2
    prices = [it.price.amount for it in res.items]
    assert all(Decimal("400") <= p <= Decimal("900") for p in prices)
