"""Integration tests for Phase 14 Responsive & Adaptive Visual System Router.

Verifies:
- All 6 FastAPI endpoints under /api/v1/visual/responsive/*
- Cross-system responsive flows across Visual Design phases VD-03 through VD-13:
  - Flow 1: Responsive Fluid Grid -> Shopping Product Listing (VD-07 P01)
  - Flow 2: Responsive Split -> Product Detail Layout (VD-09 P02)
  - Flow 3: Responsive Outfit Builder -> Styling Studio (VD-10 ST02)
  - Flow 4: Responsive Regional Map -> Geography Visuals (VD-11 M02)
  - Flow 5: Responsive AI Assistant -> Intelligence Composer (VD-12 AI02)
  - Flow 6: Responsive Preferences -> Personal Settings (VD-13 PR08)
"""

import pytest
from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------

def test_get_responsive_breakpoints_endpoint() -> None:
    """GET /api/v1/visual/responsive/breakpoints returns all 6 layout thresholds."""
    res = client.get("/api/v1/visual/responsive/breakpoints")
    assert res.status_code == 200
    bps = res.json()
    assert len(bps) == 6
    assert "xs" in bps
    assert "sm" in bps
    assert "md" in bps
    assert "lg" in bps
    assert "xl" in bps
    assert "2xl" in bps


def test_get_responsive_containers_endpoint() -> None:
    """GET /api/v1/visual/responsive/containers returns container configurations."""
    res = client.get("/api/v1/visual/responsive/containers")
    assert res.status_code == 200
    containers = res.json()
    assert len(containers) == 6
    for c in containers:
        assert c["horizontal_padding_px"] in [16, 24, 32]
        assert c["gutter_px"] >= 12
        assert c["container_max_width_px"] > 0


def test_post_evaluate_viewport_compact_mobile() -> None:
    """POST /api/v1/visual/responsive/evaluate on mobile viewport."""
    payload = {
        "width_px": 390,
        "height_px": 844,
        "input_mode": "touch",
        "prefers_reduced_motion": False,
        "safe_area_insets": {"top_px": 47, "bottom_px": 34, "left_px": 0, "right_px": 0},
    }
    res = client.post("/api/v1/visual/responsive/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["breakpoint"] == "xs"
    assert data["layout_mode"] == "compact"
    assert data["orientation"] == "portrait"
    assert data["navigation_adaptation"] == "mobile_bottom_nav_drawer"
    assert data["modal_adaptation"] == "bottom_sheet"
    assert data["filter_adaptation"] == "bottom_sheet_filter"
    assert data["outfit_builder_layout"] == "mobile_canvas_sheet"
    assert data["map_layout"] == "mobile_map_bottom_sheet"
    assert data["checkout_layout"] == "mobile_accordion_sticky"
    assert data["is_compact"] is True
    assert data["is_touch"] is True


def test_post_evaluate_viewport_tablet_adaptive() -> None:
    """POST /api/v1/visual/responsive/evaluate on tablet viewport."""
    payload = {
        "width_px": 820,
        "height_px": 1180,
        "input_mode": "touch",
    }
    res = client.post("/api/v1/visual/responsive/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["breakpoint"] == "md"
    assert data["layout_mode"] == "adaptive"
    assert data["navigation_adaptation"] == "tablet_compact_sidebar"
    assert data["modal_adaptation"] == "centered_modal"
    assert data["filter_adaptation"] == "filter_button_drawer"
    assert data["outfit_builder_layout"] == "tablet_2_column"
    assert data["is_adaptive"] is True


def test_post_evaluate_viewport_desktop_expanded() -> None:
    """POST /api/v1/visual/responsive/evaluate on desktop viewport."""
    payload = {
        "width_px": 1440,
        "height_px": 900,
        "input_mode": "mouse",
    }
    res = client.post("/api/v1/visual/responsive/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["breakpoint"] == "xl"
    assert data["layout_mode"] == "expanded"
    assert data["navigation_adaptation"] == "desktop_sidebar"
    assert data["filter_adaptation"] == "sidebar_filters"
    assert data["outfit_builder_layout"] == "desktop_3_column"
    assert data["is_expanded"] is True
    assert data["supports_hover"] is True


def test_post_calculate_fluid_grid_endpoint() -> None:
    """POST /api/v1/visual/responsive/grid-calculate computes columns dynamically."""
    payload = {
        "available_width_px": 1200,
        "card_min_width_px": 280,
        "gap_px": 16,
        "max_columns": 12,
    }
    res = client.post("/api/v1/visual/responsive/grid-calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["computed_columns"] == 4
    assert data["card_width_px"] > 280
    assert data["utilization_pct"] == 100.0


def test_post_prune_card_content_compact() -> None:
    """POST /api/v1/visual/responsive/card-prune in compact mode."""
    payload = {
        "layout_mode": "compact",
        "image_url": "https://images.fashx.studio/prod1.jpg",
        "title": "Minimalist Wool Trousers",
        "primary_action_label": "Select Size",
        "brand": "Studio Oro",
        "price_formatted": "$180.00",
        "availability": "In Stock",
        "secondary_specs": {"Material": "100% Wool", "Fit": "Relaxed"},
        "tags": ["Minimalist", "Tailored"],
    }
    res = client.post("/api/v1/visual/responsive/card-prune", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["display_brand"] is True
    assert data["display_price"] is True
    assert data["display_secondary_specs"] is False
    assert data["display_tags"] is False
    assert "secondary_specs" in data["pruned_fields"]
    assert "tags" in data["pruned_fields"]


def test_post_prune_card_content_expanded() -> None:
    """POST /api/v1/visual/responsive/card-prune in expanded mode."""
    payload = {
        "layout_mode": "expanded",
        "image_url": "https://images.fashx.studio/prod1.jpg",
        "title": "Minimalist Wool Trousers",
        "primary_action_label": "Select Size",
        "brand": "Studio Oro",
        "price_formatted": "$180.00",
        "availability": "In Stock",
        "secondary_specs": {"Material": "100% Wool", "Fit": "Relaxed"},
        "tags": ["Minimalist", "Tailored"],
    }
    res = client.post("/api/v1/visual/responsive/card-prune", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["display_secondary_specs"] is True
    assert data["display_tags"] is True
    assert len(data["pruned_fields"]) == 0


def test_get_screen_responsive_qa_endpoint() -> None:
    """GET /api/v1/visual/responsive/screen-qa/{screen_id} verifies screen responsiveness."""
    res = client.get("/api/v1/visual/responsive/screen-qa/P02?width_px=390")
    assert res.status_code == 200
    data = res.json()
    assert data["screen_id"] == "P02"
    assert data["layout_mode"] == "compact"
    assert data["has_sticky_actions"] is True
    assert data["modal_presentation"] == "bottom_sheet"


# ---------------------------------------------------------------------------
# Cross-System Integration Flows
# ---------------------------------------------------------------------------

def test_flow_01_responsive_grid_to_shopping_listing() -> None:
    """Flow 1: Responsive Grid -> Shopping Product Listing (VD-07 P01).

    Verifies fluid column calculation accurately dimensions catalog items.
    """
    # 1. Calculate grid for standard tablet (820px width)
    grid_res = client.post(
        "/api/v1/visual/responsive/grid-calculate",
        json={"available_width_px": 820 - 48, "card_min_width_px": 240, "gap_px": 16},
    )
    assert grid_res.status_code == 200
    grid_data = grid_res.json()
    assert grid_data["computed_columns"] == 3

    # 2. Fetch catalog products (P01)
    prod_res = client.get("/api/v1/visual/shopping/search?q=denim")
    assert prod_res.status_code == 200
    assert prod_res.json()["total_results"] >= 1
    assert "prod-denim-01" in prod_res.json()["product_ids"]


def test_flow_02_responsive_split_to_product_detail() -> None:
    """Flow 2: Responsive Split -> Product Detail (VD-09 P02).

    Validates sticky purchase area on mobile and side-by-side buy box on desktop.
    """
    # Mobile QA: sticky purchase active
    qa_mobile = client.get("/api/v1/visual/responsive/screen-qa/P02?width_px=375")
    assert qa_mobile.status_code == 200
    assert qa_mobile.json()["has_sticky_actions"] is True

    # Desktop QA: sticky purchase not needed; inline buy box
    qa_desktop = client.get("/api/v1/visual/responsive/screen-qa/P02?width_px=1440")
    assert qa_desktop.status_code == 200
    assert qa_desktop.json()["has_sticky_actions"] is False


def test_flow_03_responsive_outfit_builder() -> None:
    """Flow 3: Responsive Outfit Builder Layout (VD-10 ST02).

    Mobile activates canvas + bottom sheet; desktop activates 3-column layout.
    """
    # 1. Verify responsive evaluation directives
    ev_mobile = client.post("/api/v1/visual/responsive/evaluate", json={"width_px": 390, "height_px": 844})
    assert ev_mobile.json()["outfit_builder_layout"] == "mobile_canvas_sheet"

    ev_desktop = client.post("/api/v1/visual/responsive/evaluate", json={"width_px": 1440, "height_px": 900})
    assert ev_desktop.json()["outfit_builder_layout"] == "desktop_3_column"

    # 2. Verify Outfit Builder screen endpoint (ST02)
    builder_res = client.get("/api/v1/visual/styling/builder")
    assert builder_res.status_code == 200
    assert builder_res.json()["screen_id"] == "ST02"


def test_flow_04_responsive_regional_map() -> None:
    """Flow 4: Responsive Regional Map Layout (VD-11 M02).

    Mobile provides bottom sheet results; desktop provides side results panel.
    """
    ev_mobile = client.post("/api/v1/visual/responsive/evaluate", json={"width_px": 400, "height_px": 800})
    assert ev_mobile.json()["map_layout"] == "mobile_map_bottom_sheet"

    ev_desktop = client.post("/api/v1/visual/responsive/evaluate", json={"width_px": 1280, "height_px": 800})
    assert ev_desktop.json()["map_layout"] == "desktop_side_results"

    # Fetch map screen (M02)
    map_res = client.get("/api/v1/visual/geography/map")
    assert map_res.status_code == 200
    assert map_res.json()["screen_id"] == "M02"


def test_flow_05_responsive_ai_assistant() -> None:
    """Flow 5: Responsive AI Assistant (VD-12 AI02).

    Mobile pins prompt composer; desktop limits message width for scanning comfort.
    """
    qa_ai = client.get("/api/v1/visual/responsive/screen-qa/AI02?width_px=390")
    assert qa_ai.status_code == 200
    assert qa_ai.json()["has_sticky_actions"] is True

    # Check AI Assistant screen (AI02)
    ai_res = client.get("/api/v1/visual/ai/assistant")
    assert ai_res.status_code == 200
    assert ai_res.json()["screen_id"] == "AI02"


def test_flow_06_responsive_preferences() -> None:
    """Flow 6: Responsive Preferences & Personal Space (VD-13 PR08).

    Mobile provides sticky commit controls; desktop displays inline studio.
    """
    qa_pref = client.get("/api/v1/visual/responsive/screen-qa/PR08?width_px=390")
    assert qa_pref.status_code == 200
    assert qa_pref.json()["has_sticky_actions"] is True

    # Check Preferences endpoint (PR08)
    pref_res = client.get("/api/v1/visual/personal/preferences")
    assert pref_res.status_code == 200
    assert pref_res.json()["screen_id"] == "PR08"
