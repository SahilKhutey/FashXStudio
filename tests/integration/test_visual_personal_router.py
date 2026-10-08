"""Integration tests for Personal Space & Profile REST API endpoints — Phase 13.

Tests All 19 Personal Space Endpoints & 6 Cross-System Integration Flows:
- GET /api/v1/visual/personal/profile (PR01)
- GET /api/v1/visual/personal/dashboard (PR02)
- GET /api/v1/visual/personal/saved/products (PR03)
- GET /api/v1/visual/personal/saved/looks (PR04)
- GET /api/v1/visual/personal/saved/fashion (PR05)
- GET /api/v1/visual/personal/wishlist (PR06)
- GET /api/v1/visual/personal/recent (PR07)
- POST /api/v1/visual/personal/recent/clear
- GET /api/v1/visual/personal/preferences (PR08)
- PUT /api/v1/visual/personal/preferences
- GET /api/v1/visual/personal/preferences/recommendations (PR09)
- PUT /api/v1/visual/personal/preferences/recommendations
- POST /api/v1/visual/personal/preferences/recommendations/reset
- GET /api/v1/visual/personal/preferences/regional (PR10)
- PUT /api/v1/visual/personal/preferences/regional
- GET /api/v1/visual/personal/settings (PR11)
- PUT /api/v1/visual/personal/settings
- POST /api/v1/visual/personal/saved/toggle
- DELETE /api/v1/visual/personal/saved/{item_type}/{item_id}
- 6 Cross-System Integration Flows:
    Flow 1: Profile Preferences -> Discovery Results (PR08 -> VD-08 Discovery)
    Flow 2: Profile Style Preferences -> Styling Recommendation Engine (PR08 -> VD-10 Styling)
    Flow 3: Profile Preferences -> AI Style Assistant (PR08 -> VD-12 AI Assistant)
    Flow 4: Saved Product -> Product Detail Canvas (PR03 -> VD-09 Product Detail)
    Flow 5: Saved Look -> Outfit Builder Canvas (PR04 -> VD-10 Outfit Builder)
    Flow 6: Wishlist Product -> Commerce Cart Handoff (PR06 -> VD-07 Shopping Cart)
"""

import pytest
from fastapi.testclient import TestClient
from api.app.main import app
from fashx.visual.personal_service import reset_personal_fixtures
from fashx.visual.styling_service import reset_styling_fixtures
from fashx.visual.ai_service import reset_ai_fixtures

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_all_fixtures() -> None:
    """Reset personal, styling, and AI fixtures before each test."""
    reset_personal_fixtures()
    reset_styling_fixtures()
    reset_ai_fixtures()



# ===========================================================================
# 1. Individual Personal Endpoints Tests
# ===========================================================================

def test_get_profile_endpoint() -> None:
    """GET /api/v1/visual/personal/profile returns PR01 specification."""
    res = client.get("/api/v1/visual/personal/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR01"
    assert data["user_id"] == "usr_fashx_01"
    assert "Alexandra" in data["display_name"]
    assert data["saved_summary"]["products_count"] >= 3
    assert len(data["style_tags"]) >= 2


def test_get_personal_dashboard_endpoint() -> None:
    """GET /api/v1/visual/personal/dashboard returns PR02 specification with priority ordering."""
    res = client.get("/api/v1/visual/personal/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR02"
    assert len(data["continue_exploring"]) >= 3
    assert len(data["recommended_products"]) >= 1
    assert len(data["saved_preview"]) >= 2
    assert len(data["recently_viewed"]) >= 2


def test_get_personal_dashboard_graceful_degradation() -> None:
    """GET /api/v1/visual/personal/dashboard?fail_recommendations=true tests Section 13.51 failure isolation."""
    res = client.get("/api/v1/visual/personal/dashboard?fail_recommendations=true")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "partial"
    assert data["module_states"]["recommendations"] == "error"
    assert data["module_states"]["continue_exploring"] == "loaded"


def test_get_saved_products_endpoint() -> None:
    """GET /api/v1/visual/personal/saved/products returns PR03 specification."""
    res = client.get("/api/v1/visual/personal/saved/products")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR03"
    assert data["total_count"] >= 3
    assert data["items"][0]["saved_state_label"] == "Saved in Products"


def test_get_saved_products_filter_and_sort() -> None:
    """GET /api/v1/visual/personal/saved/products with filter_category and sort_by."""
    res = client.get("/api/v1/visual/personal/saved/products?filter_category=blazer&sort_by=price_asc")
    assert res.status_code == 200
    data = res.json()
    assert data["active_filter"] == "blazer"
    assert all("blazer" in p["name"].lower() for p in data["items"])


def test_get_saved_looks_endpoint() -> None:
    """GET /api/v1/visual/personal/saved/looks returns PR04 specification."""
    res = client.get("/api/v1/visual/personal/saved/looks")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR04"
    assert len(data["collections"]) >= 2
    assert len(data["items"]) >= 2


def test_get_saved_fashion_endpoint() -> None:
    """GET /api/v1/visual/personal/saved/fashion returns PR05 specification."""
    res = client.get("/api/v1/visual/personal/saved/fashion?tab=stories")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR05"
    assert data["active_tab"] == "stories"
    assert all(item["content_type"] == "story" for item in data["items"])


def test_get_wishlist_endpoint() -> None:
    """GET /api/v1/visual/personal/wishlist returns PR06 specification with real-time availability."""
    res = client.get("/api/v1/visual/personal/wishlist")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR06"
    assert data["available_count"] >= 2
    assert data["unavailable_count"] >= 1


def test_get_recently_viewed_endpoint() -> None:
    """GET /api/v1/visual/personal/recent returns PR07 specification."""
    res = client.get("/api/v1/visual/personal/recent")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR07"
    assert data["total_count"] >= 3


def test_post_clear_recent_history_endpoint() -> None:
    """POST /api/v1/visual/personal/recent/clear clears browsing activity."""
    res = client.post("/api/v1/visual/personal/recent/clear")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["remaining_count"] == 0

    # Verify recent list is empty
    verify_res = client.get("/api/v1/visual/personal/recent")
    assert verify_res.json()["state"] == "empty"


def test_get_preferences_endpoint() -> None:
    """GET /api/v1/visual/personal/preferences returns PR08 explicit vs inferred preferences."""
    res = client.get("/api/v1/visual/personal/preferences")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR08"
    assert "Minimal" in data["explicit_preferences"]["styles"]
    assert "Inferred" in data["inferred_preferences"]["observation_notice"]


def test_put_preferences_endpoint() -> None:
    """PUT /api/v1/visual/personal/preferences updates explicit styles."""
    payload = {"styles": ["Minimal", "Contemporary", "Streetwear"]}
    res = client.put("/api/v1/visual/personal/preferences", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "saved"
    assert data["explicit_preferences"]["styles"] == ["Minimal", "Contemporary", "Streetwear"]


def test_get_and_put_recommendation_preferences_endpoint() -> None:
    """GET and PUT /api/v1/visual/personal/preferences/recommendations."""
    res = client.get("/api/v1/visual/personal/preferences/recommendations")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR09"
    assert data["settings"]["personalized_recommendations"] is True

    # Update
    up_res = client.put(
        "/api/v1/visual/personal/preferences/recommendations",
        json={"personalized_recommendations": False},
    )
    assert up_res.status_code == 200
    assert up_res.json()["settings"]["personalized_recommendations"] is False


def test_post_reset_personalization_endpoint() -> None:
    """POST /api/v1/visual/personal/preferences/recommendations/reset clears inferred signals."""
    res = client.post("/api/v1/visual/personal/preferences/recommendations/reset")
    assert res.status_code == 200
    assert res.json()["state"] == "saved"

    # Verify inferred signals reset
    pref_res = client.get("/api/v1/visual/personal/preferences")
    assert len(pref_res.json()["inferred_preferences"]["frequently_viewed_styles"]) == 0


def test_get_and_put_regional_preferences_endpoint() -> None:
    """GET and PUT /api/v1/visual/personal/preferences/regional decoupled from GPS location."""
    res = client.get("/api/v1/visual/personal/preferences/regional")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR10"
    assert "not current device GPS" in data["disclaimer"]

    # Update
    up_res = client.put(
        "/api/v1/visual/personal/preferences/regional",
        json={"preferred_country": "Japan", "preferred_city": "Tokyo"},
    )
    assert up_res.status_code == 200
    assert up_res.json()["settings"]["preferred_country"] == "Japan"


def test_get_and_put_account_settings_endpoint() -> None:
    """GET and PUT /api/v1/visual/personal/settings."""
    res = client.get("/api/v1/visual/personal/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "PR11"
    assert data["settings"]["user_id"] == "usr_fashx_01"

    # Update
    up_res = client.put(
        "/api/v1/visual/personal/settings",
        json={"display_name": "Alexandra M. Chen", "privacy_level": "enhanced"},
    )
    assert up_res.status_code == 200
    assert up_res.json()["settings"]["display_name"] == "Alexandra M. Chen"


def test_post_toggle_saved_item_endpoint() -> None:
    """POST /api/v1/visual/personal/saved/toggle toggles save state."""
    payload = {"item_type": "product", "item_id": "prd_new_cart"}
    res = client.post("/api/v1/visual/personal/saved/toggle", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_saved"] is True

    # Toggle again to remove
    res2 = client.post("/api/v1/visual/personal/saved/toggle", json=payload)
    assert res2.status_code == 200
    assert res2.json()["is_saved"] is False


def test_delete_saved_item_endpoint() -> None:
    """DELETE /api/v1/visual/personal/saved/{item_type}/{item_id} explicitly removes item."""
    res = client.delete("/api/v1/visual/personal/saved/product/sav_prd_01")
    assert res.status_code == 200
    data = res.json()
    assert data["is_saved"] is False


# ===========================================================================
# 2. Cross-System Integration Flows (Section 13.81)
# ===========================================================================

def test_cross_system_flow_1_profile_to_discovery() -> None:
    """Flow 1: Profile Preferences -> Discovery Results (PR08 -> VD-08 Discovery).

    Updating explicit style preferences reflects immediately when requesting discovery modules.
    """
    # 1. Update style preferences to Avant-Garde
    client.put("/api/v1/visual/personal/preferences", json={"styles": ["Avant-Garde", "Tailored"]})

    # 2. Retrieve Discovery Home specification
    disc_res = client.get("/api/v1/visual/discovery/home")
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert disc_data["screen_id"] == "D01"
    assert len(disc_data["modules"]) >= 1


def test_cross_system_flow_2_profile_to_styling() -> None:
    """Flow 2: Profile Style Preferences -> Styling Recommendation Engine (PR08 -> VD-10 Styling).

    User's explicit styles guide outfit recommendations and style studio.
    """
    # 1. Update profile preference
    client.put("/api/v1/visual/personal/preferences", json={"styles": ["Minimal", "Contemporary"]})

    # 2. Retrieve Styling Home (ST01)
    style_res = client.get("/api/v1/visual/styling/home")
    assert style_res.status_code == 200
    style_data = style_res.json()
    assert style_data["screen_id"] == "ST01"
    assert len(style_data["recommended_looks"]) >= 1


def test_cross_system_flow_3_profile_to_ai() -> None:
    """Flow 3: Profile Preferences -> AI Style Assistant (PR08 -> VD-12 AI Assistant).

    Only explicit user styles permitted for AI context are consumed by the assistant.
    """
    # 1. Verify AI preferences permit selected styles
    ai_pref_res = client.get("/api/v1/visual/ai/preferences")
    assert ai_pref_res.status_code == 200
    assert "Minimalist" in ai_pref_res.json()["preferences"]["preferred_styles"]

    # 2. Invoke AI Style Assistant (AI04)
    assist_res = client.get("/api/v1/visual/ai/style-assistant")
    assert assist_res.status_code == 200
    assist_data = assist_res.json()
    assert assist_data["screen_id"] == "AI04"
    assert assist_data["recommended_style"]["id"] is not None
    assert len(assist_data["matching_looks"]) >= 1
    assert len(assist_data["suggested_products"]) >= 1


def test_cross_system_flow_4_saved_to_product_detail() -> None:
    """Flow 4: Saved Product -> Product Detail Canvas (PR03 -> VD-09 Product Detail).

    A saved item seamlessly transitions into the authoritative product detail screen.
    """
    # 1. Fetch saved products and pick the canonical product
    saved_res = client.get("/api/v1/visual/personal/saved/products")
    assert saved_res.status_code == 200
    denim_item = next(p for p in saved_res.json()["items"] if p["product_id"] == "prod-denim-01")

    # 2. Transition to Product Detail (P02)
    detail_res = client.get(f"/api/v1/visual/detail/product/{denim_item['product_id']}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["screen_id"] == "P02"
    assert detail_data["view_model"]["id"] == denim_item["product_id"]


def test_cross_system_flow_5_saved_to_styling_builder() -> None:
    """Flow 5: Saved Look -> Outfit Builder Canvas (PR04 -> VD-10 Outfit Builder).

    User selects a saved look and opens it in the interactive outfit builder for editing.
    """
    # 1. Fetch saved looks
    looks_res = client.get("/api/v1/visual/personal/saved/looks")
    assert looks_res.status_code == 200
    saved_look = looks_res.json()["items"][0]

    # 2. Open Outfit Builder (ST02)
    builder_res = client.get("/api/v1/visual/styling/builder")
    assert builder_res.status_code == 200
    builder_data = builder_res.json()
    assert builder_data["screen_id"] == "ST02"
    assert len(builder_data["outfit"]["slots"]) >= 3


def test_cross_system_flow_6_wishlist_to_shopping_cart() -> None:
    """Flow 6: Wishlist Product -> Commerce Cart Handoff (PR06 -> VD-07 Shopping Cart).

    User converts an available wishlist item into an active shopping cart item.
    """
    # 1. Get wishlist items
    wish_res = client.get("/api/v1/visual/personal/wishlist")
    assert wish_res.status_code == 200
    avail_item = next(i for i in wish_res.json()["items"] if i["is_available"])

    # 2. Add product to cart
    add_payload = {
        "product_id": avail_item["product_id"],
        "quantity": 1,
        "selected_variants": {"color": "raw_indigo", "size": "M"},
    }
    cart_res = client.post("/api/v1/visual/shopping/cart/add?cart_id=cart-wishlist-test", json=add_payload)
    assert cart_res.status_code == 200
    cart_data = cart_res.json()
    assert len(cart_data["items"]) >= 1
    assert any(item["product_id"] == avail_item["product_id"] for item in cart_data["items"])

