"""Integration tests for Design Token System REST API endpoints.

Tests token registry, light/dark theme resolution, Monk Skin Tone (MST) scale,
pre-bound component tokens, automated token validation, and adaptive grid calculation.
"""

from fastapi.testclient import TestClient
from fashx.main import app

client = TestClient(app)


def test_get_all_tokens() -> None:
    """GET /api/v1/visual/tokens returns complete token registry."""
    res = client.get("/api/v1/visual/tokens")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0.0"
    assert "neutral_primitives" in data
    assert "typography_scale" in data
    assert "spacing_scale" in data
    assert "radius_scale" in data
    assert "monk_skin_tones" in data


def test_get_theme_light_and_dark() -> None:
    """GET /api/v1/visual/tokens/theme resolves light and dark themes."""
    # Light theme
    res_light = client.get("/api/v1/visual/tokens/theme?mode=light")
    assert res_light.status_code == 200
    data_light = res_light.json()
    assert data_light["mode"] == "light"
    assert data_light["surfaces"]["primary"] == "#FFFFFF"
    assert data_light["content"]["primary"] == "#111827"

    # Dark theme
    res_dark = client.get("/api/v1/visual/tokens/theme?mode=dark")
    assert res_dark.status_code == 200
    data_dark = res_dark.json()
    assert data_dark["mode"] == "dark"
    assert data_dark["surfaces"]["primary"] == "#030712"
    assert data_dark["content"]["primary"] == "#F9FAFB"


def test_get_skin_tones() -> None:
    """GET /api/v1/visual/tokens/skin-tones returns Monk Skin Tone 10-point scale."""
    res = client.get("/api/v1/visual/tokens/skin-tones")
    assert res.status_code == 200
    data = res.json()
    assert data["mst_01"] == "#F6EDE4"
    assert data["mst_10"] == "#292420"
    assert data["undertone_warm"] == "#E0A96D"


def test_get_component_tokens() -> None:
    """GET /api/v1/visual/tokens/components/{name} returns bound component tokens."""
    # ProductCard
    res_pc = client.get("/api/v1/visual/tokens/components/product-card")
    assert res_pc.status_code == 200
    data_pc = res_pc.json()
    assert data_pc["surface"] == "surface.secondary"
    assert data_pc["aspect_ratio"] == "image.aspect.product"
    assert data_pc["price_typography"] == "typography.heading_s"

    # FashionCard
    res_fc = client.get("/api/v1/visual/tokens/components/fashion-card")
    assert res_fc.status_code == 200
    data_fc = res_fc.json()
    assert data_fc["aspect_ratio"] == "image.aspect.editorial"

    # Nonexistent component -> 404
    res_missing = client.get("/api/v1/visual/tokens/components/unknown-component")
    assert res_missing.status_code == 404


def test_validate_tokens_endpoint() -> None:
    """POST /api/v1/visual/tokens/validate executes WCAG and reference checks."""
    res = client.post("/api/v1/visual/tokens/validate")
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert len(data["broken_references"]) == 0
    assert len(data["contrast_checks"]) >= 6
    for check in data["contrast_checks"]:
        assert check["passes_aa"] is True


def test_grid_calculator_endpoint() -> None:
    """GET /api/v1/visual/tokens/grid-calculator calculates adaptive grid columns."""
    res = client.get("/api/v1/visual/tokens/grid-calculator?container_width_px=1024&min_card_width_px=240&gutter_px=16")
    assert res.status_code == 200
    data = res.json()
    assert data["container_width_px"] == 1024
    assert data["columns"] == 4
