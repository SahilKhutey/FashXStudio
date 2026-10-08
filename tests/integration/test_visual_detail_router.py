"""Integration tests for Product & Fashion Detail Screens REST API endpoints — Phase 09.

Tests Detail Endpoints & Journeys:
- GET /api/v1/visual/detail/product/{product_id} (P02)
- GET /api/v1/visual/detail/product/{product_id}/reviews (P05)
- GET /api/v1/visual/detail/product/{product_id}/availability (P10)
- POST /api/v1/visual/detail/product/compare (P09)
- GET /api/v1/visual/detail/fashion/story/{story_id} (F03)
- GET /api/v1/visual/detail/fashion/article/{article_id} (F04)
- GET /api/v1/visual/detail/fashion/collection/{collection_id} (F05)
- GET /api/v1/visual/detail/fashion/look/{look_id} (F06)
- GET /api/v1/visual/detail/fashion/inspiration/{inspiration_id} (F07)
- GET /api/v1/visual/detail/fashion/brand/{brand_id} (F08)
- GET /api/v1/visual/detail/fashion/editorial/{editorial_id} (F09)
- Product Journey (Section 9.68)
- Fashion Journey (Section 9.69)
- Collection & Recommendation Flow (Section 9.70 & 9.71)
"""

from fastapi.testclient import TestClient
from fashx.main import app

client = TestClient(app)


def test_product_detail_endpoint() -> None:
    """GET /api/v1/visual/detail/product/prod-denim-01 returns complete P02 template."""
    res = client.get("/api/v1/visual/detail/product/prod-denim-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "P02"
    vm = data["view_model"]
    assert vm["id"] == "prod-denim-01"
    assert vm["brand"] == "RawDenim Co."
    assert vm["price"] == 4999.0
    assert len(vm["gallery"]["items"]) >= 2
    assert len(vm["variant_groups"]) >= 2
    assert len(vm["specifications"]) >= 2
    assert len(vm["similar_products"]) >= 1
    assert len(vm["recommended_products"]) >= 1
    assert len(vm["styled_with"]) >= 1


def test_product_reviews_endpoint() -> None:
    """GET /api/v1/visual/detail/product/prod-denim-01/reviews returns P05 reviews template."""
    res = client.get("/api/v1/visual/detail/product/prod-denim-01/reviews")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "P05"
    assert data["product_id"] == "prod-denim-01"
    assert data["reviews"]["average_rating"] >= 4.0
    assert len(data["reviews"]["distribution"]) == 5
    assert len(data["reviews"]["reviews"]) >= 1


def test_product_availability_endpoint() -> None:
    """GET /api/v1/visual/detail/product/prod-denim-01/availability returns P10 availability."""
    res = client.get("/api/v1/visual/detail/product/prod-denim-01/availability")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "P10"
    assert data["availability"] == "in_stock"
    assert data["stock_units"] >= 1
    assert data["estimated_delivery_days"] >= 1


def test_product_comparison_endpoint() -> None:
    """POST /api/v1/visual/detail/product/compare returns P09 comparison matrix."""
    res = client.post(
        "/api/v1/visual/detail/product/compare",
        json=["prod-denim-01", "prod-linen-02"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "P09"
    assert len(data["comparison"]["product_ids"]) == 2
    assert len(data["comparison"]["attributes"]) >= 3


def test_fashion_story_endpoint() -> None:
    """GET /api/v1/visual/detail/fashion/story/story-coastal-layering returns F03 story."""
    res = client.get("/api/v1/visual/detail/fashion/story/story-coastal-layering")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "F03"
    assert len(data["title"]) > 0
    assert len(data["content_markdown"]) > 0
    assert len(data["related_looks"]) >= 1


def test_fashion_article_endpoint() -> None:
    """GET /api/v1/visual/detail/fashion/article/art-indigo returns F04 article."""
    res = client.get("/api/v1/visual/detail/fashion/article/art-indigo")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "F04"
    assert len(data["inline_media_uris"]) >= 2


def test_fashion_collection_endpoint() -> None:
    """GET /api/v1/visual/detail/fashion/collection/coll-monsoon-26 returns F05 collection."""
    res = client.get("/api/v1/visual/detail/fashion/collection/coll-monsoon-26")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "F05"
    assert len(data["looks"]) >= 1
    assert len(data["products"]) >= 1


def test_fashion_look_endpoint() -> None:
    """GET /api/v1/visual/detail/fashion/look/look-mumbai-01 returns F06 look with hotspots."""
    res = client.get("/api/v1/visual/detail/fashion/look/look-mumbai-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "F06"
    assert len(data["outfit_items"]) >= 2
    assert len(data["hotspots"]) >= 2
    assert "x_percent" in data["hotspots"][0]


def test_fashion_inspiration_brand_editorial_endpoints() -> None:
    """Tests F07 Inspiration, F08 Brand Story, and F09 Editorial View endpoints."""
    # F07 Inspiration
    res_insp = client.get("/api/v1/visual/detail/fashion/inspiration/insp-1")
    assert res_insp.status_code == 200
    assert res_insp.json()["screen_id"] == "F07"

    # F08 Brand Story
    res_brand = client.get("/api/v1/visual/detail/fashion/brand/brand-raw-denim")
    assert res_brand.status_code == 200
    assert res_brand.json()["screen_id"] == "F08"
    assert res_brand.json()["is_verified"] is True

    # F09 Editorial
    res_edit = client.get("/api/v1/visual/detail/fashion/editorial/edit-1")
    assert res_edit.status_code == 200
    assert res_edit.json()["screen_id"] == "F09"
    assert len(res_edit.json()["narrative_blocks"]) >= 2


def test_product_and_fashion_end_to_end_journey() -> None:
    """End-to-End User Flow (Sections 9.68 - 9.71): Product Detail -> Styled With -> Look Detail -> Constituent Product."""
    # 1. User views Product Detail for Selvedge Denim Jacket (P02)
    res_prod = client.get("/api/v1/visual/detail/product/prod-denim-01")
    assert res_prod.status_code == 200
    prod_vm = res_prod.json()["view_model"]
    assert prod_vm["id"] == "prod-denim-01"

    # 2. User checks Styled-With constituent piece
    styled_pieces = prod_vm["styled_with"]
    assert len(styled_pieces) >= 1
    partner_id = styled_pieces[0]["product_id"]

    # 3. User navigates to Look Detail (F06)
    res_look = client.get("/api/v1/visual/detail/fashion/look/look-mumbai-01")
    assert res_look.status_code == 200
    look_data = res_look.json()
    assert any(item["product_id"] == partner_id for item in look_data["outfit_items"])

    # 4. User navigates to the Partner Product (Linen Shirt)
    res_partner = client.get(f"/api/v1/visual/detail/product/{partner_id}")
    assert res_partner.status_code == 200
    assert res_partner.json()["view_model"]["id"] == partner_id
