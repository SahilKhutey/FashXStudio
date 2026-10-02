"""Integration tests for Discovery + Search Screens Experience Framework REST API endpoints — Phase 08.

Tests Discovery & Search Endpoints:
- GET /api/v1/visual/discovery/home (D01)
- GET /api/v1/visual/discovery/hero
- GET /api/v1/visual/discovery/explore/{explore_type} (D02-D08)
- GET /api/v1/visual/discovery/personalized (D09)
- GET /api/v1/visual/discovery/search-home (S01)
- GET /api/v1/visual/discovery/suggestions (S02)
- GET /api/v1/visual/discovery/search (S03-S07, S10)
- POST /api/v1/visual/discovery/advanced-search (S09)
- Exploration and search end-to-end user navigation flows
"""

from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)


def test_discovery_home_endpoint() -> None:
    """GET /api/v1/visual/discovery/home returns valid D01 Discovery Home template."""
    res = client.get("/api/v1/visual/discovery/home")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "D01"
    assert data["hero"]["id"] == "hero-monsoon-26"
    assert len(data["explore_chips"]) >= 4
    assert len(data["modules"]) >= 3


def test_discovery_hero_endpoint() -> None:
    """GET /api/v1/visual/discovery/hero returns active hero banner."""
    res = client.get("/api/v1/visual/discovery/hero")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "hero-monsoon-26"
    assert "title" in data
    assert "media_uri" in data
    assert len(data["primary_action_label"]) > 0


def test_explore_screens_endpoints() -> None:
    """GET /api/v1/visual/discovery/explore/{type} covers D02-D08."""
    expected_screens = {
        "fashion": "D02",
        "products": "D03",
        "looks": "D04",
        "collections": "D05",
        "brands": "D06",
        "styles": "D07",
        "trends": "D08",
    }
    for explore_type, expected_screen_id in expected_screens.items():
        res = client.get(f"/api/v1/visual/discovery/explore/{explore_type}")
        assert res.status_code == 200
        data = res.json()
        assert data["screen_id"] == expected_screen_id
        assert data["explore_type"] == explore_type
        assert data["total_count"] >= 1
        assert len(data["grid_items"]) >= 1


def test_personalized_discovery_endpoint() -> None:
    """GET /api/v1/visual/discovery/personalized returns D09 template with explanation."""
    res = client.get("/api/v1/visual/discovery/personalized?user_id=usr_fashion_vip")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "D09"
    assert data["user_id"] == "usr_fashion_vip"
    assert len(data["user_style_tags"]) > 0
    assert len(data["modules"]) >= 2
    assert len(data["recommendation_explanations"]) >= 1


def test_search_home_endpoint() -> None:
    """GET /api/v1/visual/discovery/search-home returns S01 gateway data."""
    res = client.get("/api/v1/visual/discovery/search-home")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "S01"
    assert len(data["recent_searches"]) >= 2
    assert len(data["trending_searches"]) >= 3
    assert len(data["explore_categories"]) >= 3


def test_search_suggestions_endpoint() -> None:
    """GET /api/v1/visual/discovery/suggestions provides autocomplete."""
    # Prefix match
    res = client.get("/api/v1/visual/discovery/suggestions?q=den")
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) >= 1
    assert any("denim" in s["text"].lower() for s in suggestions)
    assert all("suggestion_type" in s for s in suggestions)

    # Empty query fallback to popular
    res_empty = client.get("/api/v1/visual/discovery/suggestions?q=")
    assert res_empty.status_code == 200
    assert len(res_empty.json()) >= 1


def test_unified_search_across_types() -> None:
    """GET /api/v1/visual/discovery/search handles multi-content results and tabs."""
    # Search all
    res_all = client.get("/api/v1/visual/discovery/search?q=jacket&result_type=all")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["active_tab"] == "all"
    assert data_all["counts"]["all"] >= 1
    assert len(data_all["items"]) >= 1

    # Filter to products
    res_prod = client.get("/api/v1/visual/discovery/search?q=jacket&result_type=products")
    assert res_prod.status_code == 200
    data_prod = res_prod.json()
    assert data_prod["screen_id"] == "S03"
    assert data_prod["active_tab"] == "products"
    assert all(r["content_type"] == "product" for r in data_prod["items"])

    # Filter to looks
    res_look = client.get("/api/v1/visual/discovery/search?q=bandra&result_type=looks")
    assert res_look.status_code == 200
    data_look = res_look.json()
    assert data_look["screen_id"] == "S04"
    assert data_look["active_tab"] == "looks"
    assert all(r["content_type"] == "look" for r in data_look["items"])

    # Filter to brands
    res_brand = client.get("/api/v1/visual/discovery/search?q=denim&result_type=brands")
    assert res_brand.status_code == 200
    data_brand = res_brand.json()
    assert data_brand["screen_id"] == "S05"
    assert data_brand["active_tab"] == "brands"

    # Filter to styles
    res_style = client.get("/api/v1/visual/discovery/search?q=streetwear&result_type=styles")
    assert res_style.status_code == 200
    data_style = res_style.json()
    assert data_style["screen_id"] == "S06"
    assert data_style["active_tab"] == "styles"

    # Filter to trends
    res_trend = client.get("/api/v1/visual/discovery/search?q=textures&result_type=trends")
    assert res_trend.status_code == 200
    data_trend = res_trend.json()
    assert data_trend["screen_id"] == "S07"
    assert data_trend["active_tab"] == "trends"


def test_unified_search_empty_and_zero_state() -> None:
    """GET /api/v1/visual/discovery/search handles S10 zero results gracefully."""
    res = client.get("/api/v1/visual/discovery/search?q=completelynonexistentitem99999&result_type=all")
    assert res.status_code == 200
    data = res.json()
    assert data["is_empty"] is True
    assert len(data["items"]) == 0
    assert data["counts"]["all"] == 0


def test_advanced_search_endpoint() -> None:
    """POST /api/v1/visual/discovery/advanced-search executes structured multi-attribute queries (S09)."""
    payload = {
        "keywords": "denim",
        "category": "outerwear",
        "brand": "RawDenim Co.",
        "style": "Industrial Raw",
        "price_min": 2000.0,
        "price_max": 10000.0,
        "color": "Indigo",
        "size": "L",
        "region": "Japan / India",
    }
    res = client.post("/api/v1/visual/discovery/advanced-search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "S09"
    assert data["criteria"]["keywords"] == "denim"
    assert data["criteria"]["price_min"] == 2000.0
    assert len(data["preview_results"]) >= 1
    assert data["preview_results"][0]["content_type"] == "product"


def test_discovery_and_search_user_flow() -> None:
    """End-to-End User Flow: Discovery Home -> Autocomplete Suggestion -> Unified Search -> Tab Switching."""
    # 1. User loads Discovery Home (D01)
    res_home = client.get("/api/v1/visual/discovery/home")
    assert res_home.status_code == 200
    home_data = res_home.json()
    assert len(home_data["modules"]) > 0

    # 2. User starts typing query 'den' in search bar (S02 autocomplete)
    res_sugg = client.get("/api/v1/visual/discovery/suggestions?q=den")
    assert res_sugg.status_code == 200
    sugg_list = res_sugg.json()
    assert len(sugg_list) > 0
    chosen_query = sugg_list[0]["text"]

    # 3. User submits search query -> Search Results (All)
    res_results = client.get(f"/api/v1/visual/discovery/search?q={chosen_query}&result_type=all")
    assert res_results.status_code == 200
    results_data = res_results.json()
    assert results_data["active_tab"] == "all"
    assert results_data["query"] == chosen_query

    # 4. User filters by 'Products' tab
    res_prod_tab = client.get(f"/api/v1/visual/discovery/search?q={chosen_query}&result_type=products")
    assert res_prod_tab.status_code == 200
    assert res_prod_tab.json()["active_tab"] == "products"
