"""Integration tests for AI / Intelligence REST API endpoints — Phase 12.

Tests All 14 AI Endpoints & 5 Cross-System Integration Flows:
- GET /api/v1/visual/ai/home (AI01)
- POST /api/v1/visual/ai/session (Create session)
- GET /api/v1/visual/ai/session/{session_id} (Get session)
- POST /api/v1/visual/ai/session/{session_id}/message (Post message)
- GET /api/v1/visual/ai/assistant (AI02)
- GET /api/v1/visual/ai/product-assistant/{product_id} (AI03)
- GET /api/v1/visual/ai/style-assistant (AI04)
- GET /api/v1/visual/ai/outfit-recommendation (AI05)
- GET /api/v1/visual/ai/search (AI06)
- GET /api/v1/visual/ai/recommendation/{recommendation_id} (AI07)
- GET /api/v1/visual/ai/explanation/{result_id} (AI08)
- GET /api/v1/visual/ai/preferences (AI09)
- PUT /api/v1/visual/ai/preferences (Update preferences)
- POST /api/v1/visual/ai/feedback (Feedback submission)
- 5 Cross-System Integration Flows:
    Flow 1: AI Product Assistant -> Product Detail (AI03 -> VD-09 Product Detail)
    Flow 2: AI Outfit Recommendation -> Outfit Builder Canvas (AI05 -> VD-10 Styling)
    Flow 3: AI Recommendation -> Shopping Cart Handoff (AI07 -> VD-07 Commerce Cart)
    Flow 4: AI Search -> Discovery Search (AI06 -> VD-08 Discovery)
    Flow 5: AI Session Context -> Regional Geography Canvas (AI02 -> VD-11 Geography)
"""

import pytest
from fastapi.testclient import TestClient
from api.app.main import app
from fashx.visual.ai_service import reset_ai_fixtures
from fashx.visual.styling_service import reset_styling_fixtures
from fashx.visual.geography_service import reset_geography_fixtures

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_all_fixtures() -> None:
    """Reset AI, styling, and geography registries before each test."""
    reset_ai_fixtures()
    reset_styling_fixtures()
    reset_geography_fixtures()


# ===========================================================================
# 1. Individual AI Endpoints Tests
# ===========================================================================

def test_get_ai_home_endpoint() -> None:
    """GET /api/v1/visual/ai/home returns AI01 specification."""
    res = client.get("/api/v1/visual/ai/home")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI01"
    assert "Fashion Assistant" in data["hero_title"]
    assert len(data["suggested_tasks"]) == 4
    assert len(data["quick_prompts"]) >= 3
    assert len(data["curated_recommendations"]) >= 1


def test_post_create_session_endpoint() -> None:
    """POST /api/v1/visual/ai/session instantiates a new conversation session."""
    res = client.post("/api/v1/visual/ai/session?title=Summer+Wardrobe+Capsule")
    assert res.status_code == 200
    data = res.json()
    assert data["id"].startswith("session-")
    assert data["title"] == "Summer Wardrobe Capsule"
    assert len(data["context_items"]) >= 2


def test_get_session_endpoint() -> None:
    """GET /api/v1/visual/ai/session/{session_id} returns session details."""
    res = client.get("/api/v1/visual/ai/session/session-summer-trip")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "session-summer-trip"
    assert len(data["messages"]) >= 2


def test_post_session_message_endpoint() -> None:
    """POST /api/v1/visual/ai/session/{session_id}/message appends message and returns reply."""
    req_body = {
        "content": "Find lightweight shirts for high humidity",
        "context_items": [{"key": "climate", "label": "Climate", "value": "Humid", "is_removable": True}],
    }
    res = client.post("/api/v1/visual/ai/session/session-summer-trip/message", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "assistant"
    assert "verified" in data["content"].lower() or "lightweight" in data["content"].lower()
    assert len(data["citations"]) >= 1


def test_get_assistant_endpoint() -> None:
    """GET /api/v1/visual/ai/assistant returns AI02 specification."""
    res = client.get("/api/v1/visual/ai/assistant?session_id=session-summer-trip")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI02"
    assert data["session"]["id"] == "session-summer-trip"
    assert len(data["suggested_prompts"]) >= 2


def test_get_product_assistant_endpoint() -> None:
    """GET /api/v1/visual/ai/product-assistant/{id} returns AI03 with strict fact boundary."""
    res = client.get("/api/v1/visual/ai/product-assistant/prod-denim-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI03"
    assert data["product"]["id"] == "prod-denim-01"
    assert "₹4,999.00" in data["product_facts"]["Price"]
    assert "In Stock" in data["product_facts"]["Availability"]
    assert len(data["ai_guidance"]) > 10


def test_get_style_assistant_endpoint() -> None:
    """GET /api/v1/visual/ai/style-assistant returns AI04 specification."""
    res = client.get("/api/v1/visual/ai/style-assistant?style_id=style-streetwear")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI04"
    assert data["recommended_style"]["id"] == "style-streetwear"
    assert len(data["matching_looks"]) >= 1


def test_get_outfit_recommendation_endpoint() -> None:
    """GET /api/v1/visual/ai/outfit-recommendation returns AI05 specification."""
    res = client.get("/api/v1/visual/ai/outfit-recommendation?look_id=look-mumbai-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI05"
    assert data["can_edit"] is True
    assert len(data["constituent_items"]) >= 2
    assert len(data["alternatives"]) >= 1


def test_get_ai_search_endpoint() -> None:
    """GET /api/v1/visual/ai/search returns AI06 specification with intent extraction."""
    res = client.get("/api/v1/visual/ai/search?q=summer+denim+under+3000")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI06"
    assert data["interpreted_context"] == "Summer"
    assert data["interpreted_budget"] == "Under ₹3,000"
    assert data["total_results"] >= 1
    assert len(data["processing_steps"]) == 3


def test_get_recommendation_detail_endpoint() -> None:
    """GET /api/v1/visual/ai/recommendation/{id} returns AI07 specification."""
    res = client.get("/api/v1/visual/ai/recommendation/rec-summer-streetwear-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI07"
    assert data["recommendation"]["id"] == "rec-summer-streetwear-01"
    assert len(data["supporting_products"]) >= 1


def test_get_explanation_endpoint() -> None:
    """GET /api/v1/visual/ai/explanation/{id} returns AI08 specification."""
    res = client.get("/api/v1/visual/ai/explanation/rec-summer-streetwear-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "AI08"
    assert data["result_id"] == "rec-summer-streetwear-01"
    assert len(data["contributing_factors"]) >= 3


def test_get_and_put_preferences_endpoint() -> None:
    """GET and PUT /api/v1/visual/ai/preferences manages AI tuning."""
    res_get = client.get("/api/v1/visual/ai/preferences?user_id=user-default")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["screen_id"] == "AI09"
    assert "Streetwear" in data_get["preferences"]["preferred_styles"]

    # Update preferences
    payload = data_get["preferences"]
    payload["budget_tier"] = "luxury"
    payload["preferred_styles"] = ["Minimalist", "Quiet Luxury"]
    res_put = client.put("/api/v1/visual/ai/preferences", json=payload)
    assert res_put.status_code == 200
    data_put = res_put.json()
    assert data_put["budget_tier"] == "luxury"
    assert "Quiet Luxury" in data_put["preferred_styles"]


def test_post_feedback_endpoint() -> None:
    """POST /api/v1/visual/ai/feedback records structured evaluation."""
    payload = {
        "result_id": "rec-summer-streetwear-01",
        "feedback_type": "not_helpful",
        "reason": "too_expensive",
        "note": "Looking for budget tier items",
    }
    res = client.post("/api/v1/visual/ai/feedback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feedback_type"] == "not_helpful"
    assert data["reason"] == "too_expensive"


# ===========================================================================
# 2. Five Cross-System Integration Flows
# ===========================================================================

def test_cross_system_flow_1_ai_product_to_detail() -> None:
    """Flow 1: AI Product Assistant (AI03) -> Authoritative Shopping Product Detail (VD-07)."""
    # 1. Inquire with Product Assistant
    res_ai_prod = client.get("/api/v1/visual/ai/product-assistant/prod-denim-01")
    assert res_ai_prod.status_code == 200
    ai_data = res_ai_prod.json()
    prod_id = ai_data["product"]["id"]

    # 2. Transition to authoritative Commerce Product Detail
    res_shop_prod = client.get(f"/api/v1/visual/shopping/product/{prod_id}")
    assert res_shop_prod.status_code == 200
    shop_data = res_shop_prod.json()
    assert shop_data["id"] == prod_id
    assert shop_data["availability"] == "in_stock"
    assert shop_data["price"]["amount"] == 4999.0


def test_cross_system_flow_2_ai_outfit_to_builder() -> None:
    """Flow 2: AI Outfit Recommendation (AI05) -> Outfit Builder Studio (VD-10)."""
    # 1. Fetch AI outfit recommendation
    res_rec = client.get("/api/v1/visual/ai/outfit-recommendation")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    look_id = rec_data["recommended_look"]["id"]

    # 2. Hand off to Outfit Builder Studio for creative editing
    res_builder = client.get("/api/v1/visual/styling/builder")
    assert res_builder.status_code == 200
    builder_data = res_builder.json()
    assert builder_data["screen_id"] == "ST02"
    assert len(builder_data["outfit"]["slots"]) >= 5


def test_cross_system_flow_3_ai_recommendation_to_cart() -> None:
    """Flow 3: AI Recommendation (AI07) -> Select Product -> Add to Shopping Cart (VD-07)."""
    # 1. View recommendation deep dive
    res_rec = client.get("/api/v1/visual/ai/recommendation/rec-summer-streetwear-01")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    target_product = rec_data["supporting_products"][0]

    # 2. Transfer product to commerce shopping cart
    cart_id = "ai-flow-cart-1"
    add_req = {
        "product_id": target_product["id"],
        "quantity": 1,
        "selected_variants": {"color": "Raw Indigo", "size": "M"},
    }
    res_add = client.post(f"/api/v1/visual/shopping/cart/add?cart_id={cart_id}", json=add_req)
    assert res_add.status_code == 200
    cart_data = res_add.json()
    assert len(cart_data["items"]) >= 1
    assert cart_data["items"][0]["product_id"] == target_product["id"]


def test_cross_system_flow_4_ai_search_to_discovery() -> None:
    """Flow 4: AI Search (AI06) -> Intent Interpretation -> Discovery Faceted Search (VD-08)."""
    # 1. Execute natural language AI search
    res_ai_search = client.get("/api/v1/visual/ai/search?q=selvedge+denim")
    assert res_ai_search.status_code == 200
    ai_data = res_ai_search.json()
    assert ai_data["total_results"] >= 1

    # 2. Transition into Discovery catalog search
    res_discovery = client.get("/api/v1/visual/discovery/search?q=denim")
    assert res_discovery.status_code == 200
    disc_data = res_discovery.json()
    assert disc_data["screen_id"] == "S03"
    assert len(disc_data["items"]) >= 1


def test_cross_system_flow_5_ai_context_to_geography() -> None:
    """Flow 5: AI Context (AI02) -> Regional Location Profile (VD-11 Geography)."""
    # 1. Fetch assistant session with regional context
    res_assist = client.get("/api/v1/visual/ai/assistant?session_id=session-summer-trip")
    assert res_assist.status_code == 200
    assist_data = res_assist.json()
    assert len(assist_data["active_context"]) >= 1

    # 2. Bridge to regional city view
    res_geo = client.get("/api/v1/visual/geography/city/reg-raipur")
    assert res_geo.status_code == 200
    geo_data = res_geo.json()
    assert geo_data["screen_id"] == "M06"
    assert geo_data["city"]["id"] == "reg-raipur"
