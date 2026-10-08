"""Integration tests for Component Framework REST API endpoints — Phase 05."""

from fastapi.testclient import TestClient
from fashx.main import app

client = TestClient(app)


def test_get_components_catalog_contains_all_layers() -> None:
    """GET /api/v1/visual/components/catalog returns primitives, core_ui, and composites."""
    res = client.get("/api/v1/visual/components/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "primitives" in data
    assert "core_ui" in data
    assert "composites" in data
    assert len(data["primitives"]) >= 12
    assert len(data["core_ui"]) >= 14
    assert len(data["composites"]) >= 8

    # Verify L1 Primitive Box is present
    box = next((c for c in data["primitives"] if c["name"] == "Box"), None)
    assert box is not None
    assert box["taxonomy"] == "level_1_primitive"

    # Verify L3 Composite ProductCard is present
    pc = next((c for c in data["composites"] if c["name"] == "ProductCard"), None)
    assert pc is not None
    assert pc["taxonomy"] == "level_3_composite"


def test_get_component_by_name_primitive() -> None:
    """GET /api/v1/visual/components/Button returns button details."""
    res = client.get("/api/v1/visual/components/Button")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Button"
    assert data["taxonomy"] == "level_1_primitive"
    assert data["has_interactive_states"] is True


def test_get_component_by_name_composite() -> None:
    """GET /api/v1/visual/components/ProductCard returns product card details."""
    res = client.get("/api/v1/visual/components/ProductCard")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "ProductCard"
    assert data["taxonomy"] == "level_3_composite"


def test_get_component_case_insensitive() -> None:
    """GET /api/v1/visual/components/fashioncard succeeds regardless of casing."""
    res = client.get("/api/v1/visual/components/fashioncard")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "FashionCard"


def test_get_component_not_found() -> None:
    """GET /api/v1/visual/components/UnknownWidget returns 404."""
    res = client.get("/api/v1/visual/components/UnknownWidget")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_validate_props_valid_product_card() -> None:
    """POST /api/v1/visual/components/validate for ProductCard returns valid report."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=ProductCard",
        json={
            "product_id": "p-101",
            "title": "Tailored Blazer",
            "brand": "Massimo Dutti",
            "image_uri": "https://images.fashx.com/blazer.jpg",
            "price": {"amount": 8990.0, "currency_symbol": "₹"},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["component_name"] == "ProductCard"
    assert data["validated_props"]["title"] == "Tailored Blazer"


def test_validate_props_valid_recommendation_card() -> None:
    """POST /api/v1/visual/components/validate for RecommendationCard returns valid report."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=RecommendationCard",
        json={
            "recommendation_id": "rec-01",
            "product": {
                "product_id": "p-102",
                "title": "Linen Trousers",
                "brand": "Uniqlo",
                "image_uri": "https://images.fashx.com/trousers.jpg",
                "price": {"amount": 2990.0},
            },
            "explanation": "Complements your recent purchase of the relaxed linen shirt",
            "confidence_score": 0.88,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert "linen shirt" in data["validated_props"]["explanation"]


def test_validate_props_extra_field_forbidden() -> None:
    """POST /api/v1/visual/components/validate strictly rejects extra arbitrary props."""
    res = client.post(
        "/api/v1/visual/components/validate?component_name=Box",
        json={"padding": "space.2", "unauthorized_css_property": "red"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("extra" in err.lower() for err in data["errors"])
