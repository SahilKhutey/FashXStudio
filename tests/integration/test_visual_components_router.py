"""Integration tests for Component Framework REST API endpoints — Phase 05."""

from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)


def test_get_components_catalog() -> None:
    """GET /api/v1/visual/components/catalog returns primitives and core_ui."""
    res = client.get("/api/v1/visual/components/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "primitives" in data
    assert "core_ui" in data
    assert len(data["primitives"]) >= 7
    assert len(data["core_ui"]) >= 6

    # Verify Button is in primitives
    btn = next((c for c in data["primitives"] if c["name"] == "Button"), None)
    assert btn is not None
    assert "primary" in btn["available_variants"]
    assert any("2.5.8" in wcag for wcag in btn["wcag_criteria"])


def test_get_component_by_name_success() -> None:
    """GET /api/v1/visual/components/Button returns component details."""
    res = client.get("/api/v1/visual/components/Button")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Button"
    assert data["taxonomy"] == "level_1_primitive"
    assert data["has_interactive_states"] is True


def test_get_component_by_name_case_insensitive() -> None:
    """GET /api/v1/visual/components/card succeeds regardless of casing."""
    res = client.get("/api/v1/visual/components/card")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Card"
    assert data["taxonomy"] == "level_2_core_ui"


def test_get_component_not_found() -> None:
    """GET /api/v1/visual/components/UnknownWidget returns 404."""
    res = client.get("/api/v1/visual/components/UnknownWidget")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_validate_props_valid_button() -> None:
    """POST /api/v1/visual/components/validate for valid button returns valid report."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Button",
        json={"label": "Add to Wardrobe", "variant": "primary", "size": "md"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["component_name"] == "Button"
    assert len(data["errors"]) == 0
    assert data["validated_props"]["label"] == "Add to Wardrobe"


def test_validate_props_invalid_missing_required() -> None:
    """POST /api/v1/visual/components/validate fails when required prop missing."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Button",
        json={"variant": "outline"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


def test_validate_props_invalid_extra_field() -> None:
    """POST /api/v1/visual/components/validate rejects extra fields (extra='forbid')."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Button",
        json={"label": "Try On", "unauthorized_prop": "error"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("extra" in err.lower() for err in data["errors"])


def test_validate_props_valid_input() -> None:
    """POST /api/v1/visual/components/validate for Input returns valid report."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Input",
        json={"label": "Search Garments", "placeholder": "Silk, Cashmere...", "input_type": "search"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["validated_props"]["input_type"] == "search"


def test_validate_props_rating_out_of_bounds() -> None:
    """POST /api/v1/visual/components/validate rejects rating > 5.0."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Rating",
        json={"value": 6.5},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
