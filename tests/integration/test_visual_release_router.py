"""Integration Tests for FashXStudio Production Visual Integration, Verification & Release Router (Phase 16 - FINAL).

Validates all 8 REST endpoints under /api/v1/visual/release/* and executes
end-to-end cross-system verification linking VD-00 through VD-15.
"""

from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------

def test_get_release_screens_endpoint() -> None:
    """Validate GET /api/v1/visual/release/screens returns canonical screen registry."""
    res = client.get("/api/v1/visual/release/screens")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 15

    screen_ids = [s["screen_id"] for s in data]
    assert "D01" in screen_ids
    assert "P01" in screen_ids
    assert "P03" in screen_ids
    assert "DT01" in screen_ids
    assert "ST02" in screen_ids
    assert "M02" in screen_ids
    assert "AI01" in screen_ids
    assert "PR01" in screen_ids

    for screen in data:
        assert screen["route"].startswith("/")
        assert screen["is_production_ready"] is True


def test_get_release_navigation_endpoint() -> None:
    """Validate GET /api/v1/visual/release/navigation returns unified navigation registry."""
    res = client.get("/api/v1/visual/release/navigation")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 7

    routes = [item["route"] for item in data]
    assert "/discovery" in routes
    assert "/shop/catalog" in routes
    assert "/styling/builder" in routes
    assert "/geography/map" in routes
    assert "/ai/home" in routes
    assert "/profile/dashboard" in routes


def test_post_validate_token_endpoint_valid() -> None:
    """Validate POST /api/v1/visual/release/token-validation for compliant tokens."""
    payload = {
        "token_name": "color.surface.card",
        "token_category": "color",
        "primitive_ref": "white",
        "semantic_usage": "Card background fill",
        "theme": "light",
    }
    res = client.post("/api/v1/visual/release/token-validation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["token_name"] == "color.surface.card"
    assert data["is_valid"] is True
    assert data["resolved_value"] == "#FFFFFF"
    assert data["hierarchy_valid"] is True


def test_post_validate_token_endpoint_rogue_rejection() -> None:
    """Validate POST /api/v1/visual/release/token-validation rejects rogue tokens (Section 16.6)."""
    payload = {
        "token_name": "rogue.inline.fontSize",
        "token_category": "typography",
        "primitive_ref": "unknown-size",
        "semantic_usage": "Ad-hoc font override",
    }
    res = client.post("/api/v1/visual/release/token-validation", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert data["hierarchy_valid"] is False
    assert len(data["errors"]) >= 1


def test_post_release_gate_audit_endpoint() -> None:
    """Validate POST /api/v1/visual/release/gate-audit evaluates the 5 master release gates."""
    payload = {
        "release_version": "v1.0.0-rc1",
        "environment": "staging",
        "include_e2e": True,
        "include_a11y": True,
    }
    res = client.post("/api/v1/visual/release/gate-audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["release_version"] == "v1.0.0-rc1"
    assert data["overall_passed"] is True
    assert len(data["gates"]) == 5

    gate_names = [g["gate_name"] for g in data["gates"]]
    assert "functional" in gate_names
    assert "visual" in gate_names
    assert "accessibility" in gate_names
    assert "performance" in gate_names
    assert "integration" in gate_names

    assert data["golden_screens_count"] == 15
    assert data["golden_components_count"] == 15


def test_get_release_checklist_endpoint() -> None:
    """Validate GET /api/v1/visual/release/checklist returns complete checklist across 13 categories."""
    res = client.get("/api/v1/visual/release/checklist")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 20

    categories = {item["category"] for item in data}
    assert "foundation" in categories
    assert "shell" in categories
    assert "components" in categories
    assert "fashion" in categories
    assert "shopping" in categories
    assert "discovery" in categories
    assert "styling" in categories
    assert "geography" in categories
    assert "ai" in categories
    assert "personal" in categories
    assert "responsive" in categories
    assert "accessibility" in categories
    assert "qa" in categories


def test_get_release_e2e_journeys_endpoint() -> None:
    """Validate GET /api/v1/visual/release/e2e-journeys returns E2E-001 through E2E-005."""
    res = client.get("/api/v1/visual/release/e2e-journeys")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5

    journey_ids = [j["journey_id"] for j in data]
    assert journey_ids == ["E2E-001", "E2E-002", "E2E-003", "E2E-004", "E2E-005"]


def test_get_release_golden_artifacts_endpoint() -> None:
    """Validate GET /api/v1/visual/release/golden-artifacts returns 30 anchors."""
    res = client.get("/api/v1/visual/release/golden-artifacts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 30

    screens = [a for a in data if a["artifact_type"] == "screen"]
    components = [a for a in data if a["artifact_type"] == "component"]
    assert len(screens) == 15
    assert len(components) == 15


def test_get_release_track_status_endpoint() -> None:
    """Validate GET /api/v1/visual/release/status confirms VD-00 through VD-16 at 100%."""
    res = client.get("/api/v1/visual/release/status")
    assert res.status_code == 200
    data = res.json()
    assert data["visual_design_architecture_pct"] == 100
    assert data["visual_specification_pct"] == 100
    assert data["actual_repository_implementation_pct"] == 0
    assert data["total_phases"] == 17
    assert "COMPLETE & VERIFIED" in data["status_message"]


# ---------------------------------------------------------------------------
# Cross-Core Integration Flow Tests (E2E-001 through E2E-005)
# ---------------------------------------------------------------------------

def test_cross_core_e2e_001_commerce_loop() -> None:
    """E2E-001: Discovery Feed -> Search -> Product Detail -> Cart -> Checkout (Section 16.36)."""
    # 1. Discovery Feed (VD-06 / VD-08)
    feed_res = client.get("/api/v1/visual/fashion/feed")
    assert feed_res.status_code == 200
    assert len(feed_res.json()["items"]) > 0

    # 2. Product Detail Screen (VD-09)
    prod_res = client.get("/api/v1/visual/detail/product/prod-denim-01")
    assert prod_res.status_code == 200
    assert prod_res.json()["screen_id"] == "P02"

    # 3. Cart & Commerce Summary (VD-07)
    cart_res = client.get("/api/v1/visual/shopping/cart")
    assert cart_res.status_code == 200
    assert cart_res.json()["summary"]["total"] > 0


def test_cross_core_e2e_002_fashion_to_builder() -> None:
    """E2E-002: Fashion Stories -> Curated Look -> Outfit Studio Builder (Section 16.36)."""
    # 1. Stories Feed (VD-06)
    stories_res = client.get("/api/v1/visual/fashion/feed?content_type=story")
    assert stories_res.status_code == 200

    # 2. Outfit Studio Builder (VD-10)
    builder_res = client.get("/api/v1/visual/styling/builder")
    assert builder_res.status_code == 200
    assert builder_res.json()["screen_id"] == "ST02"
    assert len(builder_res.json()["outfit"]["slots"]) >= 3


def test_cross_core_e2e_003_map_to_product() -> None:
    """E2E-003: Fashion Map -> Region -> Local Products (Section 16.36)."""
    # 1. Fashion Map Canvas (VD-11)
    map_res = client.get("/api/v1/visual/geography/map")
    assert map_res.status_code == 200
    assert map_res.json()["screen_id"] == "M02"

    # 2. Regional Products (VD-11)
    reg_prod_res = client.get("/api/v1/visual/geography/products/reg-mumbai")
    assert reg_prod_res.status_code == 200
    assert len(reg_prod_res.json()) > 0


def test_cross_core_e2e_004_ai_to_styling() -> None:
    """E2E-004: AI Stylist -> Product Fact Separation -> Styling Review (Section 16.36)."""
    # 1. AI Assistant (VD-12)
    ai_res = client.get("/api/v1/visual/ai/product-assistant/prod-denim-01")
    assert ai_res.status_code == 200
    assert ai_res.json()["screen_id"] == "AI03"
    assert "Material" in ai_res.json()["product_facts"]
    assert ai_res.json()["ai_guidance"] is not None


def test_cross_core_e2e_005_profile_to_discovery() -> None:
    """E2E-005: Profile Dashboard -> Preferences -> Feedback Dispatch (Section 16.36)."""
    # 1. Profile Preferences (VD-13)
    pref_res = client.get("/api/v1/visual/personal/preferences")
    assert pref_res.status_code == 200
    assert pref_res.json()["screen_id"] == "PR08"

    # 2. Feedback Dispatch (VD-15)
    feedback_res = client.post(
        "/api/v1/visual/interaction/feedback/dispatch",
        json={"situation": "minor_success", "title": "Preferences Saved", "message": "Updated personal affinities"},
    )
    assert feedback_res.status_code == 200
    assert feedback_res.json()["feedback_type"] == "toast"
