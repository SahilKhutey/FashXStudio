from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from database.models.catalog_embeddings import ProductImageEmbeddingRecord
from database.models.catalog_image import (
    CatalogImageAsset,
    CatalogImageTakedown,
    ImageAssetStatus,
    ImageTakedownStatus,
)
from database.models.catalog_search import ProductSearchDocumentRecord
from fashx.catalog.search.availability import filter_availability_and_takedowns
from fashx.catalog.search.contracts import (
    ProductSearchRequest,
    VisualSearchRequest,
)
from fashx.catalog.search.ranking import apply_business_ranking
from fashx.catalog.search.search_service import FashionSearchService
from fashx.catalog.search.visual_search import execute_visual_search


def test_srch_021_visual_search_retrieval(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-021: Visual search retrieves visually similar items by image asset."""
    session = search_sync_session
    cat = setup_search_catalog
    asset1 = cat["asset1"]
    mp3 = cat["mp3"]
    merch_a = cat["merch_a"]
    source_a = cat["source_a"]

    # Create a 3rd asset associated with mp3 that has identical vector to asset1
    emb1_rec = session.query(ProductImageEmbeddingRecord).filter_by(image_asset_id=asset1.id).first()
    assert emb1_rec is not None

    asset3 = CatalogImageAsset(
        id=uuid4(),
        source_id=source_a.id,
        merchant_id=merch_a.id,
        source_product_id="SKU-TEE-03",
        status=ImageAssetStatus.ACTIVE.value,
        original_sha256="sha_img_3",
        normalized_sha256="sha_img_3",
    )
    session.add(asset3)
    session.flush()

    img_emb3 = ProductImageEmbeddingRecord(
        id=uuid4(),
        image_asset_id=asset3.id,
        product_id=mp3.id,
        merchant_id=merch_a.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=emb1_rec.embedding,
        image_sha256="sha_img_3",
        status="ACTIVE",
        is_active=True,
    )
    session.add(img_emb3)
    session.commit()

    service = FashionSearchService()
    req = VisualSearchRequest(query_image_asset_id=asset1.id, limit=5)
    res = service.visual_search(session, req)

    assert res.total >= 1
    assert any(it.merchant_product_id == mp3.id for it in res.items)


def test_srch_022_unauthorized_query_image_rejected(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-022: Inactive or unauthorized image asset is rejected."""
    session = search_sync_session
    cat = setup_search_catalog
    merch_a = cat["merch_a"]
    source_a = cat["source_a"]

    unauthorized_asset = CatalogImageAsset(
        id=uuid4(),
        source_id=source_a.id,
        merchant_id=merch_a.id,
        source_product_id="SKU-REJECTED",
        status="REJECTED",
        original_sha256="sha_rej",
        normalized_sha256="sha_rej",
    )
    session.add(unauthorized_asset)
    session.commit()

    with pytest.raises(PermissionError, match="not authorized"):
        execute_visual_search(session, unauthorized_asset.id)


def test_srch_023_ranking_title_brand_boost(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-023: Exact title and brand match receives positive rank multiplier."""
    cat = setup_search_catalog
    mp1 = cat["mp1"]
    mp3 = cat["mp3"]
    brand_roadster = cat["brand_roadster"]

    doc1 = search_sync_session.query(ProductSearchDocumentRecord).filter_by(merchant_product_id=mp1.id).first()
    doc3 = search_sync_session.query(ProductSearchDocumentRecord).filter_by(merchant_product_id=mp3.id).first()
    assert doc1 is not None and doc3 is not None

    candidates = [(mp1.id, 1.0), (mp3.id, 1.0)]
    search_docs = {mp1.id: doc1, mp3.id: doc3}
    brand_map = {brand_roadster.id: "Roadster"}

    boosted = apply_business_ranking(
        candidates=candidates,
        query_text="Men's Black Casual Shirt",
        search_docs=search_docs,
        brand_map=brand_map,
    )

    # mp1 exact title match should rank first with score > mp3
    assert boosted[0][0] == mp1.id
    assert boosted[0][1] > boosted[1][1]


def test_srch_024_sorting_modes(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-024: Sorting by price low-to-high and high-to-low."""
    service = FashionSearchService()

    # Price low-to-high: mp3 (499) <= mp1 (899) <= mp2 (1499)
    req_asc = ProductSearchRequest(sort="price_low", limit=10)
    res_asc = service.search(search_sync_session, req_asc)
    assert len(res_asc.items) >= 2
    prices_asc = [it.price.amount for it in res_asc.items]
    assert prices_asc == sorted(prices_asc)

    # Price high-to-low: mp2 (1499) >= mp1 (899) >= mp3 (499)
    req_desc = ProductSearchRequest(sort="price_high", limit=10)
    res_desc = service.search(search_sync_session, req_desc)
    assert len(res_desc.items) >= 2
    prices_desc = [it.price.amount for it in res_desc.items]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_srch_025_cursor_pagination_zero_duplicates(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-025: Cursor pagination returns disjoint pages with zero duplicates."""
    service = FashionSearchService()

    # Page 1: limit 1
    req1 = ProductSearchRequest(limit=1)
    res1 = service.search(search_sync_session, req1)
    assert len(res1.items) == 1
    assert res1.next_cursor is not None

    # Page 2: with cursor
    req2 = ProductSearchRequest(cursor=res1.next_cursor, limit=1)
    res2 = service.search(search_sync_session, req2)
    assert len(res2.items) == 1

    # Disjoint IDs
    page1_ids = {it.merchant_product_id for it in res1.items}
    page2_ids = {it.merchant_product_id for it in res2.items}
    assert page1_ids.isdisjoint(page2_ids)


def test_srch_026_invalid_cursor_rejected(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-026: Malformed or non-existent cursor token is safely rejected."""
    service = FashionSearchService()

    with pytest.raises(ValueError, match="Invalid cursor token"):
        service.search(search_sync_session, ProductSearchRequest(cursor="completely_invalid_garbage"))


def test_srch_027_no_results_helpful_suggestions(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-027: Zero result search includes actionable, non-empty suggestions."""
    service = FashionSearchService()
    req = ProductSearchRequest(q="nonexistent_alien_spacesuit_xyz")
    res = service.search(search_sync_session, req)

    assert res.total == 0
    assert len(res.items) == 0
    assert res.suggestions is not None
    assert len(res.suggestions) >= 1


def test_srch_028_unavailable_product_excluded(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-028: Inactive or delisted products are strictly excluded from search."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]

    # Mark mp1 inactive
    mp1.status = "archived"
    session.commit()

    service = FashionSearchService()
    req = ProductSearchRequest(q="Black Casual Shirt")
    res = service.search(session, req)

    assert not any(it.merchant_product_id == mp1.id for it in res.items)

    # Revert mp1 status
    mp1.status = "active"
    session.commit()


def test_srch_029_takedown_product_hard_exclusion(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-029: Approved takedown excludes product from search candidate set."""
    session = search_sync_session
    cat = setup_search_catalog
    mp1 = cat["mp1"]

    # Add active takedown on source_a
    takedown = CatalogImageTakedown(
        id=uuid4(),
        source_id=cat["source_a"].id,
        merchant_id=cat["merch_a"].id,
        scope_type="source",
        scope_target=str(cat["source_a"].id),
        reason_code="IP_INFRINGEMENT",
        status=ImageTakedownStatus.PROCESSING.value,
    )
    session.add(takedown)
    session.commit()

    valid = filter_availability_and_takedowns(session, [mp1.id])
    assert mp1.id not in valid

    # Clean up
    session.delete(takedown)
    session.commit()


def test_srch_030_stale_offer_excluded(
    search_sync_session: Session, setup_search_catalog: dict[str, Any]
) -> None:
    """Verify SRCH-030: Products with stale/inactive merchant offers are excluded."""
    session = search_sync_session
    cat = setup_search_catalog
    offer1 = cat["offer1"]

    offer1.status = "EXPIRED"
    session.commit()

    service = FashionSearchService()
    req = ProductSearchRequest(q="Black Casual Shirt")
    res = service.search(session, req)

    # mp1 has no active offer, so it should not appear in hydrated results
    assert not any(it.merchant_product_id == cat["mp1"].id for it in res.items)

    # Revert offer status
    offer1.status = "ACTIVE"
    session.commit()
