"""Integration tests for Fashion Content System REST API endpoints — Phase 06."""

from fastapi.testclient import TestClient
from fashx.main import app

client = TestClient(app)


def test_get_fashion_feed_all() -> None:
    """GET /api/v1/visual/fashion/feed returns multi-object feed without filter."""
    res = client.get("/api/v1/visual/fashion/feed")
    assert res.status_code == 200
    data = res.json()
    assert "feed_id" in data
    assert "title" in data
    assert "items" in data
    assert "total_items" in data
    assert data["total_items"] >= 5
    assert len(data["items"]) >= 5

    # Verify polymorphic content types exist in feed
    types_in_feed = {item["content_type"] for item in data["items"]}
    assert "story" in types_in_feed
    assert "look" in types_in_feed
    assert "product" in types_in_feed
    assert "trend" in types_in_feed
    assert "collection" in types_in_feed


def test_get_fashion_feed_filtered_by_type() -> None:
    """GET /api/v1/visual/fashion/feed?content_type=product returns only products."""
    res = client.get("/api/v1/visual/fashion/feed?content_type=product")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) >= 1
    for item in data["items"]:
        assert item["content_type"] == "product"
        assert item["price"] is not None


def test_get_fashion_feed_with_limit() -> None:
    """GET /api/v1/visual/fashion/feed?limit=2 returns at most 2 items."""
    res = client.get("/api/v1/visual/fashion/feed?limit=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2


def test_get_fashion_content_product() -> None:
    """GET /api/v1/visual/fashion/content/product/prod-denim-01 returns product domain item."""
    res = client.get("/api/v1/visual/fashion/content/product/prod-denim-01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "prod-denim-01"
    assert data["title"] == "Selvedge Oversized Denim Jacket"
    assert data["brand"] == "RawDenim Co."
    assert data["price"]["amount"] == 4999.0
    assert data["price"]["original_amount"] == 6999.0
    assert data["is_in_stock"] is True
    assert data["badge"] == "BESTSELLER"


def test_get_fashion_content_look() -> None:
    """GET /api/v1/visual/fashion/content/look/look-mumbai-01 returns look domain item."""
    res = client.get("/api/v1/visual/fashion/content/look/look-mumbai-01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "look-mumbai-01"
    assert data["title"] == "Bandra Sunday Street Style"
    assert data["curator_name"] == "Aarav Mehta"
    assert len(data["associated_product_ids"]) == 2


def test_get_fashion_content_outfit() -> None:
    """GET /api/v1/visual/fashion/content/outfit/outfit-monsoon-01 returns ensemble with slots."""
    res = client.get("/api/v1/visual/fashion/content/outfit/outfit-monsoon-01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "outfit-monsoon-01"
    assert len(data["pieces"]) == 2
    slots = [p["slot"] for p in data["pieces"]]
    assert "outerwear" in slots
    assert "top" in slots


def test_get_fashion_content_trend() -> None:
    """GET /api/v1/visual/fashion/content/trend/trend-raw-textures returns trend with timeline."""
    res = client.get("/api/v1/visual/fashion/content/trend/trend-raw-textures")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "trend-raw-textures"
    assert data["momentum"] == "emerging"
    assert len(data["timeline"]) == 3
    assert data["timeline"][0]["signal_label"] == "Runway emergence"


def test_get_fashion_content_recommendation() -> None:
    """GET /api/v1/visual/fashion/content/recommendation/rec-denim-jacket returns AI recommendation."""
    res = client.get("/api/v1/visual/fashion/content/recommendation/rec-denim-jacket")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "rec-denim-jacket"
    assert data["confidence_score"] == 0.94
    assert "selvedge denim" in data["explanation_reason"].lower()


def test_get_fashion_content_not_found() -> None:
    """GET /api/v1/visual/fashion/content/product/non-existent returns 404."""
    res = client.get("/api/v1/visual/fashion/content/product/non-existent")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_save_toggle_endpoint_save_and_unsave() -> None:
    """POST /api/v1/visual/fashion/save-toggle correctly executes state transitions."""
    # First toggle: Save item
    save_req = {
        "content_type": "product",
        "content_id": "prod-denim-01",
        "current_saved": False,
    }
    res1 = client.post("/api/v1/visual/fashion/save-toggle", json=save_req)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["content_id"] == "prod-denim-01"
    assert data1["content_type"] == "product"
    assert data1["is_saved"] is True
    assert data1["state"] == "saved"
    assert "saved to your wardrobe" in data1["message"]

    # Second toggle: Unsave item
    unsave_req = {
        "content_type": "product",
        "content_id": "prod-denim-01",
        "current_saved": True,
    }
    res2 = client.post("/api/v1/visual/fashion/save-toggle", json=unsave_req)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["content_id"] == "prod-denim-01"
    assert data2["content_type"] == "product"
    assert data2["is_saved"] is False
    assert data2["state"] == "unsaved"
    assert "removed from your wardrobe" in data2["message"]


def test_get_discovery_template() -> None:
    """GET /api/v1/visual/fashion/templates/discovery returns complete multi-section layout."""
    res = client.get("/api/v1/visual/fashion/templates/discovery")
    assert res.status_code == 200
    data = res.json()
    assert "featured_story" in data
    assert "trending_items" in data
    assert "curated_collections" in data
    assert "recommended_products" in data
    assert "featured_brands" in data

    assert data["featured_story"]["title"] == "The Art of Coastal Humidity Layering"
    assert len(data["trending_items"]) >= 1
    assert len(data["curated_collections"]) >= 1
    assert len(data["recommended_products"]) >= 1
    assert len(data["featured_brands"]) >= 1


def test_get_listing_template_default() -> None:
    """GET /api/v1/visual/fashion/templates/listing returns default catalog listing spec."""
    res = client.get("/api/v1/visual/fashion/templates/listing")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Explore All"
    assert len(data["items"]) >= 1
    assert len(data["sort_options"]) >= 4
    assert data["selected_sort"] == "Relevance"
    assert data["current_page"] == 1


def test_get_listing_template_with_category() -> None:
    """GET /api/v1/visual/fashion/templates/listing?category=outerwear returns formatted category."""
    res = client.get("/api/v1/visual/fashion/templates/listing?category=outerwear")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Explore Outerwear"
    assert len(data["items"]) >= 1
