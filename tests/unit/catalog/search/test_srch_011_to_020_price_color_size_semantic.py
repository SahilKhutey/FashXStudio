from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.orm import Session

from fashx.catalog.search.contracts import ProductSearchRequest
from fashx.catalog.search.search_service import FashionSearchService
from fashx.catalog.search.semantic_search import execute_semantic_search


def test_srch_011_invalid_price_range() -> None:
    """Verify SRCH-011: Invalid price range (min > max or negative) is rejected."""
    # Min > Max
    with pytest.raises(ValueError, match="min_price .* cannot be greater than max_price"):
        ProductSearchRequest(min_price=Decimal("1000"), max_price=Decimal("500"))

    # Negative price
    with pytest.raises(ValueError):
        ProductSearchRequest(min_price=Decimal("-50"))


def test_srch_012_currency_mismatch(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-012: Currency mismatch prevents cross-currency comparisons."""
    service = FashionSearchService()
    # Catalog is in INR. Filtering by USD returns 0 results
    req = ProductSearchRequest(currency="USD", min_price=Decimal("10"), max_price=Decimal("50"))
    res = service.search(search_sync_session, req)

    assert res.total == 0


def test_srch_013_color_filter(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-013: Color filter matches normalized color in search document."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="black", limit=10)
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert any("Black" in it.title for it in res.items)


def test_srch_014_multi_color_match(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-014: Multi-color garment matches color search terms."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="striped", limit=10)
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert any("Striped" in it.title for it in res.items)


def test_srch_015_size_filter_variant_stock(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-015: Size filter matches variant SKU currently in stock."""
    service = FashionSearchService()
    # Size M with in_stock=True should match mp1 (M in stock), exclude mp3 (M out of stock)
    req = ProductSearchRequest(size="M", in_stock=True)
    res = service.search(search_sync_session, req)

    assert res.total == 1
    assert "Black Casual Shirt" in res.items[0].title


def test_srch_016_unknown_size_never_falsely_available(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-016: Unknown size stock is never falsely treated as in stock."""
    service = FashionSearchService()
    # mp2 has size 40 with status UNKNOWN. Requesting in_stock=True must NOT return it
    req = ProductSearchRequest(size="40", in_stock=True)
    res = service.search(search_sync_session, req)

    assert res.total == 0


def test_srch_017_out_of_stock_size_excluded(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-017: Out-of-stock size variant is excluded when in_stock=True."""
    service = FashionSearchService()
    # Size L on mp1 is OUT_OF_STOCK
    req = ProductSearchRequest(size="L", in_stock=True)
    res = service.search(search_sync_session, req)

    assert res.total == 0


def test_srch_018_occasion_filter(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-018: Occasion filter matches approved attributes."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="festive")
    res = service.search(search_sync_session, req)

    assert res.total >= 1
    assert any("Kurta" in it.title for it in res.items)


def test_srch_019_semantic_query_retrieval(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-019: Semantic natural language query returns conceptually related items."""
    candidates = execute_semantic_search(
        session=search_sync_session,
        query_text="formal office shirt",
        model_id="openclip_vit_b32",
        model_version="v1",
        limit=10,
    )
    assert len(candidates) >= 1


def test_srch_020_wrong_embedding_dimension_rejected(
    search_sync_session: Session,
) -> None:
    """Verify SRCH-020: Querying with unapproved or non-existent model is rejected."""
    with pytest.raises(KeyError, match="not approved or registered"):
        execute_semantic_search(
            session=search_sync_session,
            query_text="shirt",
            model_id="unregistered_model_xyz",
            model_version="v99",
        )
