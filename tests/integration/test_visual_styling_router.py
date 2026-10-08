"""Integration tests for Outfit / Styling REST API endpoints — Phase 10.

Tests All 18 Styling Endpoints & 5 Core User Journeys:
- GET /api/v1/visual/styling/home (ST01)
- GET /api/v1/visual/styling/builder (ST02)
- POST /api/v1/visual/styling/builder/{outfit_id}/add (Add item to slot)
- POST /api/v1/visual/styling/builder/{outfit_id}/replace (Replace slot item)
- DELETE /api/v1/visual/styling/builder/{outfit_id}/slot/{slot_id} (Remove slot item)
- POST /api/v1/visual/styling/builder/{outfit_id}/reset (Reset outfit slots)
- GET /api/v1/visual/styling/look-builder (ST03)
- GET /api/v1/visual/styling/mix-match (ST04)
- GET /api/v1/visual/styling/recommendation (ST05)
- GET /api/v1/visual/styling/preview/{outfit_id} (ST06)
- GET /api/v1/visual/styling/detail/{outfit_id} (ST07)
- GET /api/v1/visual/styling/validate-shop/{outfit_id} (Pre-purchase validation)
- GET /api/v1/visual/styling/saved-looks (ST08)
- POST /api/v1/visual/styling/saved-looks (Save outfit as look)
- POST /api/v1/visual/styling/saved-looks/{look_id}/duplicate (Duplicate look)
- DELETE /api/v1/visual/styling/saved-looks/{look_id} (Delete look)
- GET /api/v1/visual/styling/preferences (ST09)
- PUT /api/v1/visual/styling/preferences (Update preferences)
- 5 Cross-System Integration Flows (Product->Builder, Discovery->Builder, Builder->Saved, Builder->Shopping, AI->Builder)
"""

import pytest
from fastapi.testclient import TestClient
from fashx.main import app
from fashx.visual.styling_service import INITIAL_OUTFIT, reset_styling_fixtures

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_styling_fixtures() -> None:
    """Reset outfit registry before each test to guarantee state isolation."""
    reset_styling_fixtures()


def test_styling_home_endpoint() -> None:
    """GET /api/v1/visual/styling/home returns ST01 template."""
    res = client.get("/api/v1/visual/styling/home")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "ST01"
    assert data["featured_style"]["id"] == "style-streetwear"
    assert len(data["popular_styles"]) >= 1
    assert len(data["recommended_looks"]) >= 1
    assert len(data["saved_looks_preview"]) >= 1


def test_styling_builder_endpoint() -> None:
    """GET /api/v1/visual/styling/builder returns ST02 template."""
    res = client.get(f"/api/v1/visual/styling/builder?outfit_id={INITIAL_OUTFIT.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "ST02"
    assert data["outfit"]["id"] == INITIAL_OUTFIT.id
    assert len(data["outfit"]["slots"]) >= 5
    assert len(data["available_categories"]) == 6


def test_slot_mutation_endpoints() -> None:
    """Test slot item mutations: add, replace, remove, and reset endpoints."""
    outfit_id = INITIAL_OUTFIT.id

    # Reset slots
    res_reset = client.post(f"/api/v1/visual/styling/builder/{outfit_id}/reset")
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["total_price"] == 0.0

    # Add slot item
    payload_add = {
        "slot_id": "slot-top",
        "product_id": "prod-linen-02",
        "selected_variants": {"color": "sand", "size": "L"},
    }
    res_add = client.post(f"/api/v1/visual/styling/builder/{outfit_id}/add", json=payload_add)
    assert res_add.status_code == 200
    add_data = res_add.json()
    top_slot = next(s for s in add_data["slots"] if s["id"] == "slot-top")
    assert top_slot["item"]["product_id"] == "prod-linen-02"
    assert add_data["total_price"] == 2499.0

    # Replace slot item
    payload_replace = {
        "slot_id": "slot-top",
        "new_product_id": "prod-denim-01",
        "selected_variants": {"color": "raw_indigo", "size": "M"},
    }
    res_replace = client.post(f"/api/v1/visual/styling/builder/{outfit_id}/replace", json=payload_replace)
    assert res_replace.status_code == 200
    replace_data = res_replace.json()
    top_slot_rep = next(s for s in replace_data["slots"] if s["id"] == "slot-top")
    assert top_slot_rep["item"]["product_id"] == "prod-denim-01"
    assert replace_data["total_price"] == 4999.0

    # Remove slot item
    res_remove = client.delete(f"/api/v1/visual/styling/builder/{outfit_id}/slot/slot-top")
    assert res_remove.status_code == 200
    remove_data = res_remove.json()
    top_slot_rem = next(s for s in remove_data["slots"] if s["id"] == "slot-top")
    assert top_slot_rem["item"] is None
    assert remove_data["total_price"] == 0.0


def test_look_builder_endpoint() -> None:
    """GET /api/v1/visual/styling/look-builder returns ST03 template."""
    res = client.get("/api/v1/visual/styling/look-builder?look_id=look-mumbai-01")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "ST03"
    assert data["look_id"] == "look-mumbai-01"
    assert len(data["visual_items"]) >= 2


def test_mix_match_endpoint() -> None:
    """GET /api/v1/visual/styling/mix-match returns ST04 matrix template."""
    res = client.get(f"/api/v1/visual/styling/mix-match?outfit_id={INITIAL_OUTFIT.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "ST04"
    assert data["matrix"]["outfit_id"] == INITIAL_OUTFIT.id
    assert len(data["matrix"]["candidates_by_slot"]) >= 4


def test_style_recommendation_endpoint() -> None:
    """GET /api/v1/visual/styling/recommendation returns ST05 explainable recommendation."""
    res = client.get("/api/v1/visual/styling/recommendation?user_id=user-1")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "ST05"
    assert len(data["recommended_looks"]) >= 1
    assert len(data["recommended_products"]) >= 1


def test_outfit_preview_and_detail_endpoints() -> None:
    """GET ST06 preview and ST07 detail endpoints."""
    outfit_id = INITIAL_OUTFIT.id

    # ST06 Preview
    res_prev = client.get(f"/api/v1/visual/styling/preview/{outfit_id}")
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["screen_id"] == "ST06"
    assert prev_data["outfit"]["id"] == outfit_id

    # ST07 Detail
    res_det = client.get(f"/api/v1/visual/styling/detail/{outfit_id}")
    assert res_det.status_code == 200
    det_data = res_det.json()
    assert det_data["screen_id"] == "ST07"
    assert len(det_data["constituent_items"]) >= 1
    assert len(det_data["similar_outfits"]) >= 1


def test_validate_shop_endpoint() -> None:
    """GET /api/v1/visual/styling/validate-shop/{outfit_id} checks pre-purchase stock integrity."""
    res = client.get(f"/api/v1/visual/styling/validate-shop/{INITIAL_OUTFIT.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["outfit_id"] == INITIAL_OUTFIT.id
    assert data["can_proceed_to_cart"] is True
    assert data["available_items"] >= 1


def test_saved_looks_endpoints() -> None:
    """Test ST08 saved looks listing, save, duplicate, and delete endpoints."""
    # List
    res_list = client.get("/api/v1/visual/styling/saved-looks?user_id=user-1")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["screen_id"] == "ST08"
    assert data["total_saved"] >= 1

    # Save current outfit
    save_payload = {
        "outfit_id": INITIAL_OUTFIT.id,
        "name": "Evening Contemporary Minimal",
        "user_id": "user-1",
        "collection_tag": "capsule",
    }
    res_save = client.post("/api/v1/visual/styling/saved-looks", json=save_payload)
    assert res_save.status_code == 200
    saved_item = res_save.json()
    assert saved_item["name"] == "Evening Contemporary Minimal"

    # Duplicate
    res_dup = client.post(f"/api/v1/visual/styling/saved-looks/{saved_item['id']}/duplicate")
    assert res_dup.status_code == 200
    dup_item = res_dup.json()
    assert "(Copy)" in dup_item["name"]

    # Delete
    res_del = client.delete(f"/api/v1/visual/styling/saved-looks/{dup_item['id']}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True


def test_style_preferences_endpoints() -> None:
    """Test ST09 style preferences retrieval and update."""
    # Retrieve
    res_get = client.get("/api/v1/visual/styling/preferences?user_id=user-1")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["screen_id"] == "ST09"
    assert len(data["available_styles"]) >= 3

    # Update
    update_payload = {
        "user_id": "user-1",
        "preferred_styles": ["Minimalism", "Scandinavian"],
        "preferred_fits": ["Tailored"],
        "preferred_colors": ["White", "Charcoal"],
        "preferred_materials": ["Cashmere", "Wool"],
        "budget_tier": "premium",
    }
    res_put = client.put("/api/v1/visual/styling/preferences?user_id=user-1", json=update_payload)
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["budget_tier"] == "premium"
    assert "Scandinavian" in updated["preferred_styles"]


# ---------------------------------------------------------------------------
# Cross-System Integration Flows (Sections 10.45 - 10.49)
# ---------------------------------------------------------------------------

def test_flow_01_product_to_builder() -> None:
    """Flow 1 (Section 10.45): Product detail -> Add to slot in Outfit Builder."""
    # 1. Fetch product detail
    res_prod = client.get("/api/v1/visual/detail/product/prod-denim-01")
    assert res_prod.status_code == 200
    prod = res_prod.json()["view_model"]

    # 2. Add product directly to outfit outerwear slot
    res_add = client.post(
        f"/api/v1/visual/styling/builder/{INITIAL_OUTFIT.id}/add",
        json={"slot_id": "slot-outerwear", "product_id": prod["id"]},
    )
    assert res_add.status_code == 200
    outfit = res_add.json()
    outerwear_slot = next(s for s in outfit["slots"] if s["id"] == "slot-outerwear")
    assert outerwear_slot["item"]["product_id"] == "prod-denim-01"


def test_flow_02_discovery_to_builder() -> None:
    """Flow 2 (Section 10.46): Discovery look -> Look Builder."""
    res_look = client.get("/api/v1/visual/styling/look-builder?look_id=look-mumbai-01")
    assert res_look.status_code == 200
    look = res_look.json()
    assert look["look_id"] == "look-mumbai-01"
    assert len(look["visual_items"]) >= 2


def test_flow_03_builder_to_saved_looks() -> None:
    """Flow 3 (Section 10.47): Outfit Builder -> Persist to Saved Looks archive."""
    res_save = client.post(
        "/api/v1/visual/styling/saved-looks",
        json={
            "outfit_id": INITIAL_OUTFIT.id,
            "name": "Persisted Monochromatic Look",
            "user_id": "user-flow",
            "collection_tag": "capsule",
        },
    )
    assert res_save.status_code == 200
    saved = res_save.json()
    assert saved["name"] == "Persisted Monochromatic Look"

    # Verify queryable in user saved looks
    res_list = client.get("/api/v1/visual/styling/saved-looks?user_id=user-flow")
    assert res_list.status_code == 200
    assert any(lk["id"] == saved["id"] for lk in res_list.json()["saved_looks"])


def test_flow_04_builder_to_shopping_cart() -> None:
    """Flow 4 (Section 10.48): Outfit Builder -> Validate Stock -> Hand off to Cart."""
    # 1. Validate outfit availability
    res_val = client.get(f"/api/v1/visual/styling/validate-shop/{INITIAL_OUTFIT.id}")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["can_proceed_to_cart"] is True

    # 2. Add available products present in catalog to shopping cart
    shoppable_pids = [pid for pid in val_data["available_product_ids"] if pid in ("prod-denim-01", "prod-linen-02")]
    for pid in shoppable_pids:
        res_cart = client.post(
            "/api/v1/visual/shopping/cart/add?cart_id=cart-styling-integration",
            json={"product_id": pid, "quantity": 1},
        )
        assert res_cart.status_code == 200

    # 3. Verify cart state
    res_cart_state = client.get("/api/v1/visual/shopping/cart?cart_id=cart-styling-integration")
    assert res_cart_state.status_code == 200
    cart_data = res_cart_state.json()
    assert cart_data["summary"]["item_count"] >= len(shoppable_pids)


def test_flow_05_ai_recommendation_to_builder() -> None:
    """Flow 5 (Section 10.49): AI Style Recommendation -> Adopt curated product into Outfit Builder."""
    # 1. Fetch recommendation
    res_rec = client.get("/api/v1/visual/styling/recommendation?user_id=user-1")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert len(rec_data["recommended_products"]) > 0
    rec_prod_id = rec_data["recommended_products"][0]["id"]

    # 2. Adopt recommended product into outfit builder top slot
    res_adopt = client.post(
        f"/api/v1/visual/styling/builder/{INITIAL_OUTFIT.id}/add",
        json={"slot_id": "slot-top", "product_id": rec_prod_id},
    )
    assert res_adopt.status_code == 200
    outfit = res_adopt.json()
    top_slot = next(s for s in outfit["slots"] if s["id"] == "slot-top")
    assert top_slot["item"]["product_id"] == rec_prod_id
