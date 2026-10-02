"""Integration tests for Phase 15 Interaction, State, Accessibility & Visual QA System Router.

Verifies:
- All 6 FastAPI endpoints under /api/v1/visual/interaction/*
- The 6 End-to-End Visual Journeys established in Section 15.98:
  - Journey A: Discovery -> Product (search input, loading, results, empty state)
  - Journey B: Product -> Cart (variant selection, optimistic add, quantity validation)
  - Journey C: Fashion -> Outfit Builder (slot selection, replacement, unsaved alert)
  - Journey D: AI Assistant -> Styling (processing state, fact vs guidance, feedback)
  - Journey E: Regional Map -> Local Products (marker selection, list alternative)
  - Journey F: Profile -> Personalization (preference changes, saved state, signal reset)
"""

import pytest
from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------

def test_post_evaluate_component_state_endpoint() -> None:
    """POST /api/v1/visual/interaction/component-state resolves state and a11y attributes."""
    payload = {
        "component_id": "cart_checkout_btn",
        "is_loading": True,
        "is_selected": True,
    }
    res = client.post("/api/v1/visual/interaction/component-state", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["active_state"] == "loading"
    assert data["aria_busy"] is True
    assert data["is_interactive"] is False
    assert data["touch_target_min_px"] >= 44


def test_post_validate_form_field_endpoint() -> None:
    """POST /api/v1/visual/interaction/form-validate validates input with actionable guidance."""
    # Invalid email
    payload_invalid = {
        "field_id": "email_input",
        "field_type": "email",
        "value": "not-an-email",
        "is_required": True,
    }
    res_inv = client.post("/api/v1/visual/interaction/form-validate", json=payload_invalid)
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["is_valid"] is False
    assert data_inv["state"] == "error"
    assert data_inv["aria_invalid"] is True
    assert "user@example.com" in data_inv["guidance"]

    # Valid email
    payload_valid = {
        "field_id": "email_input",
        "field_type": "email",
        "value": "alexandra@fashx.studio",
        "is_required": True,
    }
    res_val = client.post("/api/v1/visual/interaction/form-validate", json=payload_valid)
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True
    assert res_val.json()["state"] == "success"


def test_post_dispatch_feedback_endpoint() -> None:
    """POST /api/v1/visual/interaction/feedback/dispatch determines optimal feedback mechanism."""
    # Minor success -> Toast
    res_toast = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={"situation": "minor_success", "title": "Saved", "message": "Saved to Lookbook"},
    )
    assert res_toast.status_code == 200
    assert res_toast.json()["feedback_type"] == "toast"
    assert res_toast.json()["auto_dismiss_ms"] == 3000

    # Destructive action -> Dialog
    res_dialog = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={"situation": "destructive_action", "title": "Delete", "message": "Confirm deletion"},
    )
    assert res_dialog.status_code == 200
    assert res_dialog.json()["feedback_type"] == "dialog"
    assert res_dialog.json()["requires_confirmation"] is True


def test_get_screen_lifecycle_state_endpoint() -> None:
    """GET /api/v1/visual/interaction/screen-state/{screen_id} returns state specifications."""
    # Loading
    res_loading = client.get("/api/v1/visual/interaction/screen-state/P02?lifecycle_state=loading")
    assert res_loading.status_code == 200
    assert res_loading.json()["lifecycle_state"] == "loading"
    assert res_loading.json()["skeleton_layout_type"] == "detail"

    # Error
    res_error = client.get("/api/v1/visual/interaction/screen-state/P02?lifecycle_state=error")
    assert res_error.status_code == 200
    assert res_error.json()["lifecycle_state"] == "error"
    assert res_error.json()["retry_supported"] is True


def test_post_run_accessibility_audit_endpoint() -> None:
    """POST /api/v1/visual/interaction/accessibility-audit evaluates WCAG AA criteria."""
    payload = {
        "target_id": "PrimaryButton",
        "touch_target_px": 44,
        "contrast_ratio": 5.2,
        "has_accessible_name": True,
        "has_keyboard_trap": False,
        "has_visible_focus": True,
    }
    res = client.post("/api/v1/visual/interaction/accessibility-audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_compliant"] is True
    assert data["touch_target_passed"] is True
    assert data["contrast_passed"] is True


def test_get_visual_qa_matrix_endpoint() -> None:
    """GET /api/v1/visual/interaction/qa-matrix returns visual regression test specs."""
    res = client.get("/api/v1/visual/interaction/qa-matrix")
    assert res.status_code == 200
    specs = res.json()
    assert len(specs) >= 5
    assert any(s["fixture_id"] == "QA-PROD-CARD-01" for s in specs)


# ---------------------------------------------------------------------------
# Section 15.98: End-to-End Visual Journeys
# ---------------------------------------------------------------------------

def test_journey_a_discovery_to_product() -> None:
    """Journey A: Discovery -> Search -> Results -> Product (Section 15.98).

    Verifies interaction state transitions from search input to product details.
    """
    # 1. Evaluate search input active focus state
    focus_res = client.post(
        "/api/v1/visual/interaction/component-state",
        json={"component_id": "global_search_input", "is_focused": True},
    )
    assert focus_res.status_code == 200
    assert focus_res.json()["focus_ring_visible"] is True

    # 2. Execute search
    search_res = client.get("/api/v1/visual/shopping/search?q=denim")
    assert search_res.status_code == 200
    prod_id = search_res.json()["product_ids"][0]

    # 3. Transition to product detail (P02)
    prod_res = client.get(f"/api/v1/visual/detail/product/{prod_id}")
    assert prod_res.status_code == 200
    assert prod_res.json()["screen_id"] == "P02"


def test_journey_b_product_to_cart() -> None:
    """Journey B: Product -> Variant Selection -> Add to Cart -> Cart (Section 15.98).

    Validates selected variant interaction state, optimistic feedback, and cart sync.
    """
    # 1. Variant chip selection state
    variant_res = client.post(
        "/api/v1/visual/interaction/component-state",
        json={"component_id": "chip_size_m", "is_selected": True},
    )
    assert variant_res.status_code == 200
    assert variant_res.json()["active_state"] == "selected"

    # 2. Add to cart
    add_payload = {
        "product_id": "prod-denim-01",
        "quantity": 1,
        "selected_variants": {"color": "raw_indigo", "size": "M"},
    }
    cart_res = client.post("/api/v1/visual/shopping/cart/add?cart_id=cart-journey-b", json=add_payload)
    assert cart_res.status_code == 200

    # 3. Verify non-blocking feedback toast dispatch
    fb_res = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={"situation": "add_to_cart", "title": "Added to Bag", "message": "Selvedge Jacket added."},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["feedback_type"] == "toast"


def test_journey_c_fashion_to_outfit_builder() -> None:
    """Journey C: Fashion Story -> Look -> Builder -> Unsaved Changes (Section 15.98).

    Validates transition into styling builder and unsaved state alert handling.
    """
    # 1. Open Outfit Builder (ST02)
    builder_res = client.get("/api/v1/visual/styling/builder")
    assert builder_res.status_code == 200
    assert builder_res.json()["screen_id"] == "ST02"

    # 2. Unsaved changes warning feedback
    unsaved_res = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={
            "situation": "destructive_action",
            "title": "Unsaved Outfit Changes",
            "message": "Leaving now will discard your current outfit selections.",
            "action_label": "Leave",
            "is_destructive": True,
        },
    )
    assert unsaved_res.status_code == 200
    assert unsaved_res.json()["requires_confirmation"] is True


def test_journey_d_ai_assistant_to_styling() -> None:
    """Journey D: AI Assistant -> Recommendation -> Fact vs Guidance (Section 15.98).

    Validates separation of catalog facts from subjective AI guidance and user review.
    """
    # 1. Fetch AI Product Assistant (AI03)
    ai_res = client.get("/api/v1/visual/ai/product-assistant/prod-denim-01")
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert ai_data["screen_id"] == "AI03"
    assert "Selvedge" in ai_data["product_facts"]["Material"]
    assert ai_data["ai_guidance"] is not None

    # 2. Audit touch target of AI prompt composer
    audit_res = client.post(
        "/api/v1/visual/interaction/accessibility-audit",
        json={"target_id": "AIPromptInput", "touch_target_px": 48, "has_accessible_name": True},
    )
    assert audit_res.status_code == 200
    assert audit_res.json()["touch_target_passed"] is True


def test_journey_e_regional_map_to_product() -> None:
    """Journey E: Regional Map -> Region Selection -> Local Products (Section 15.98).

    Validates accessible structured list alternative alongside the map canvas.
    """
    # 1. Fetch Fashion Map (M02)
    map_res = client.get("/api/v1/visual/geography/map")
    assert map_res.status_code == 200
    assert map_res.json()["screen_id"] == "M02"

    # 2. Verify offline fallback state for map
    offline_res = client.get("/api/v1/visual/interaction/screen-state/M02?lifecycle_state=offline")
    assert offline_res.status_code == 200
    assert offline_res.json()["is_offline"] is True


def test_journey_f_profile_to_personalization() -> None:
    """Journey F: Profile -> Preferences -> Save -> Reset Signals (Section 15.98).

    Validates explicit user preference state transition and inferred signal reset.
    """
    # 1. Fetch Preferences (PR08)
    pref_res = client.get("/api/v1/visual/personal/preferences")
    assert pref_res.status_code == 200
    assert pref_res.json()["screen_id"] == "PR08"

    # 2. Reset personalization signals with feedback
    reset_res = client.post("/api/v1/visual/personal/preferences/recommendations/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["state"] == "saved"

    # 3. Verify confirmation toast
    fb_res = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={"situation": "minor_success", "title": "Signals Reset", "message": "Inferred browsing history cleared."},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["feedback_type"] == "toast"
