"""Integration tests for Regional Maps & Geography REST API endpoints — Phase 11.

Tests All 13 Geography Endpoints & 5 Cross-System Integration Flows:
- GET /api/v1/visual/geography/home (M01)
- GET /api/v1/visual/geography/map (M02)
- GET /api/v1/visual/geography/explorer (M03)
- GET /api/v1/visual/geography/country/{country_id} (M04)
- GET /api/v1/visual/geography/state/{state_id} (M05)
- GET /api/v1/visual/geography/city/{city_id} (M06)
- GET /api/v1/visual/geography/trends/{region_id} (M07)
- GET /api/v1/visual/geography/products/{region_id} (M08)
- GET /api/v1/visual/geography/collections/{region_id} (M09)
- GET /api/v1/visual/geography/location/{location_id} (M10)
- GET /api/v1/visual/geography/search
- POST /api/v1/visual/geography/compare
- GET /api/v1/visual/geography/breadcrumbs/{region_id}
- 5 Cross-System Integration Flows:
    Flow 1: Map -> Region Drilldown (M02 -> M06)
    Flow 2: Region -> Trend Discovery (M06 -> M07)
    Flow 3: Region -> Product -> Shopping Cart (M08 -> VD-07 Cart)
    Flow 4: Region -> Look -> Outfit Builder (M10 -> VD-10 Styling Builder)
    Flow 5: Search -> Region Explorer Drilldown (Search -> M03)
"""

import pytest
from fastapi.testclient import TestClient
from fashx.main import app
from fashx.visual.geography_service import reset_geography_fixtures
from fashx.visual.styling_service import INITIAL_OUTFIT, reset_styling_fixtures

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_geography_fixtures() -> None:
    """Reset geography and styling registry fixtures before each test."""
    reset_geography_fixtures()
    reset_styling_fixtures()


# ===========================================================================
# 1. Individual Geography Endpoints Tests
# ===========================================================================

def test_get_geography_home_endpoint() -> None:
    """GET /api/v1/visual/geography/home returns M01 specification."""
    res = client.get("/api/v1/visual/geography/home")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M01"
    assert data["featured_region"]["id"] == "reg-india"
    assert len(data["popular_regions"]) >= 4
    assert data["featured_map"]["state"] == "ready"
    assert len(data["regional_trends"]) >= 1
    assert len(data["local_products"]) >= 1


def test_get_geography_map_endpoint() -> None:
    """GET /api/v1/visual/geography/map returns M02 specification."""
    res = client.get("/api/v1/visual/geography/map?region_id=reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M02"
    assert data["selected_region"]["id"] == "reg-raipur"
    assert len(data["map_view"]["markers"]) >= 5
    assert len(data["map_view"]["clusters"]) >= 2
    assert "regions" in data["available_layers"]
    assert "trends" in data["available_layers"]


def test_get_geography_explorer_endpoint_modes() -> None:
    """GET /api/v1/visual/geography/explorer returns M03 specification."""
    # Root level
    res_root = client.get("/api/v1/visual/geography/explorer")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["screen_id"] == "M03"
    assert all(r["type"] == "country" for r in data_root["regions"])

    # Child drilldown
    res_child = client.get("/api/v1/visual/geography/explorer?parent_id=reg-india")
    assert res_child.status_code == 200
    data_child = res_child.json()
    assert data_child["parent_region"]["id"] == "reg-india"
    assert len(data_child["breadcrumbs"]) == 1
    assert any(r["id"] == "reg-chhattisgarh" for r in data_child["regions"])

    # Search query
    res_search = client.get("/api/v1/visual/geography/explorer?q=Okayama")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert len(data_search["regions"]) == 1
    assert data_search["regions"][0]["id"] == "reg-okayama"


def test_get_geography_country_endpoint() -> None:
    """GET /api/v1/visual/geography/country/{id} returns M04 specification."""
    res = client.get("/api/v1/visual/geography/country/reg-india")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M04"
    assert data["country"]["id"] == "reg-india"
    assert len(data["states_or_provinces"]) >= 3
    assert len(data["breadcrumbs"]) == 1


def test_get_geography_state_endpoint() -> None:
    """GET /api/v1/visual/geography/state/{id} returns M05 specification."""
    res = client.get("/api/v1/visual/geography/state/reg-chhattisgarh")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M05"
    assert data["state_region"]["id"] == "reg-chhattisgarh"
    assert data["country_region"]["id"] == "reg-india"
    assert any(c["id"] == "reg-raipur" for c in data["cities"])


def test_get_geography_city_endpoint() -> None:
    """GET /api/v1/visual/geography/city/{id} returns M06 specification."""
    res = client.get("/api/v1/visual/geography/city/reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M06"
    assert data["city"]["id"] == "reg-raipur"
    assert len(data["fashion_trends"]) >= 1
    assert len(data["related_cities"]) >= 1


def test_get_geography_trends_endpoint() -> None:
    """GET /api/v1/visual/geography/trends/{id} returns M07 specification."""
    res = client.get("/api/v1/visual/geography/trends/reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M07"
    assert data["region"]["id"] == "reg-raipur"
    assert len(data["trends"]) >= 1


def test_get_geography_products_endpoint() -> None:
    """GET /api/v1/visual/geography/products/{id} returns M08 specification."""
    res = client.get("/api/v1/visual/geography/products/reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M08"
    assert data["region"]["id"] == "reg-raipur"
    assert data["total_count"] == len(data["products"])
    assert len(data["available_filters"]) >= 2


def test_get_geography_collections_endpoint() -> None:
    """GET /api/v1/visual/geography/collections/{id} returns M09 specification."""
    res = client.get("/api/v1/visual/geography/collections/reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M09"
    assert data["featured_collection"] is not None
    assert len(data["collections"]) >= 1


def test_get_geography_location_endpoint() -> None:
    """GET /api/v1/visual/geography/location/{id} returns M10 specification."""
    res = client.get("/api/v1/visual/geography/location/reg-raipur")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "M10"
    assert data["location"]["id"] == "reg-raipur"
    assert data["map_view"]["selected_region_id"] == "reg-raipur"
    assert len(data["breadcrumbs"]) == 3


def test_get_geography_search_endpoint() -> None:
    """GET /api/v1/visual/geography/search returns matching region contracts."""
    res = client.get("/api/v1/visual/geography/search?q=selvedge&region_type=city")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["id"] == "reg-kojima"
    assert data[0]["type"] == "city"


def test_post_geography_compare_endpoint() -> None:
    """POST /api/v1/visual/geography/compare returns side-by-side comparison matrix."""
    req_body = ["reg-raipur", "reg-kojima", "reg-paris"]
    res = client.post("/api/v1/visual/geography/compare", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["region_ids"] == req_body
    assert len(data["regions"]) == 3
    assert len(data["metrics"]) >= 3
    # Check textile craft values across regions
    metric_textile = next((m for m in data["metrics"] if m["name"] == "Primary Textile Craft"), None)
    assert metric_textile is not None
    assert "Kosa" in metric_textile["values_by_region"]["reg-raipur"]
    assert "Denim" in metric_textile["values_by_region"]["reg-kojima"]


def test_get_geography_breadcrumbs_endpoint() -> None:
    """GET /api/v1/visual/geography/breadcrumbs/{id} returns root-to-leaf path."""
    res = client.get("/api/v1/visual/geography/breadcrumbs/reg-raipur")
    assert res.status_code == 200
    crumbs = res.json()
    assert len(crumbs) == 3
    assert [c["id"] for c in crumbs] == ["reg-india", "reg-chhattisgarh", "reg-raipur"]
    assert crumbs[2]["is_current"] is True


# ===========================================================================
# 2. Five Cross-System Integration Flows
# ===========================================================================

def test_cross_system_flow_1_map_to_region_drilldown() -> None:
    """Flow 1: Map (M02) -> Marker Tap -> City View (M06) with Breadcrumbs."""
    # 1. Fetch Fashion Map
    res_map = client.get("/api/v1/visual/geography/map")
    assert res_map.status_code == 200
    map_data = res_map.json()
    # 2. Pick a city marker
    raipur_marker = next(
        (m for m in map_data["map_view"]["markers"] if m["region_id"] == "reg-raipur"),
        None,
    )
    assert raipur_marker is not None
    target_region_id = raipur_marker["region_id"]

    # 3. Drill down to City View
    res_city = client.get(f"/api/v1/visual/geography/city/{target_region_id}")
    assert res_city.status_code == 200
    city_data = res_city.json()
    assert city_data["city"]["id"] == "reg-raipur"
    assert len(city_data["breadcrumbs"]) == 3


def test_cross_system_flow_2_region_to_trend_discovery() -> None:
    """Flow 2: City View (M06) -> Select Local Trend -> Dedicated Trends Feed (M07)."""
    # 1. View city
    res_city = client.get("/api/v1/visual/geography/city/reg-raipur")
    assert res_city.status_code == 200
    city_data = res_city.json()
    assert len(city_data["fashion_trends"]) >= 1
    selected_trend = city_data["fashion_trends"][0]

    # 2. Navigate to Regional Trends Feed
    res_trends = client.get(f"/api/v1/visual/geography/trends/{selected_trend['region_id']}")
    assert res_trends.status_code == 200
    trends_data = res_trends.json()
    assert any(t["id"] == selected_trend["id"] for t in trends_data["trends"])


def test_cross_system_flow_3_region_to_product_to_cart() -> None:
    """Flow 3: Region Products (M08) -> Product Selection -> Add to Shopping Cart (VD-07)."""
    # 1. View regional products for Raipur
    res_products = client.get("/api/v1/visual/geography/products/reg-raipur")
    assert res_products.status_code == 200
    prod_data = res_products.json()
    assert len(prod_data["products"]) >= 1
    first_product = prod_data["products"][0]

    # 2. Add product to commerce cart
    add_req = {
        "product_id": first_product["id"],
        "quantity": 2,
        "selected_variants": {"color": "Natural Ecru", "size": "L"},
    }
    cart_id = "geo-flow-cart-1"
    res_cart_add = client.post(f"/api/v1/visual/shopping/cart/add?cart_id={cart_id}", json=add_req)
    assert res_cart_add.status_code == 200
    cart_result = res_cart_add.json()
    assert len(cart_result["items"]) >= 1
    assert cart_result["items"][0]["product_id"] == first_product["id"]
    assert cart_result["items"][0]["quantity"] == 2


def test_cross_system_flow_4_region_to_look_to_outfit_builder() -> None:
    """Flow 4: Location Detail (M10) -> Curated Look -> Outfit Builder Canvas (VD-10)."""
    # 1. View location profile
    res_loc = client.get("/api/v1/visual/geography/location/reg-raipur")
    assert res_loc.status_code == 200
    loc_data = res_loc.json()
    assert len(loc_data["looks"]) >= 1
    look_id = loc_data["looks"][0]["id"]

    # 2. Inspect Look Builder for styling integration
    res_look_builder = client.get(f"/api/v1/visual/styling/look-builder?look_id={look_id}")
    assert res_look_builder.status_code == 200
    lb_data = res_look_builder.json()
    assert lb_data["screen_id"] == "ST03"
    assert lb_data["look_id"] == look_id


def test_cross_system_flow_5_search_to_region_explorer() -> None:
    """Flow 5: Global Geography Search -> Explore Hierarchy Subtree (M03)."""
    # 1. Search for Kojima Denim capital
    res_search = client.get("/api/v1/visual/geography/search?q=Kojima")
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) >= 1
    found_city = results[0]
    parent_id = found_city["parent_id"]

    # 2. Open Explorer at parent state level (Okayama)
    res_explorer = client.get(f"/api/v1/visual/geography/explorer?parent_id={parent_id}")
    assert res_explorer.status_code == 200
    exp_data = res_explorer.json()
    assert exp_data["parent_region"]["id"] == parent_id
    assert any(r["id"] == found_city["id"] for r in exp_data["regions"])
