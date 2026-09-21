from fastapi.testclient import TestClient

from api.app.main import app


def test_feature_routes_publish_the_registry_and_availability() -> None:
    client = TestClient(app)

    listing = client.get("/api/v1/features")
    availability = client.get("/api/v1/features/FX-F01")

    assert listing.status_code == 200
    assert listing.json()[0]["id"] == "FX-F00"
    assert availability.status_code == 200
    assert availability.json()["available"] is True


def test_runtime_route_initializes_features_with_explicit_states() -> None:
    response = TestClient(app).get("/api/v1/features/runtime")

    assert response.status_code == 200
    assert response.json()[0] == {
        "feature_id": "FX-F00",
        "lifecycle": "ready",
        "state": "ready",
        "enabled_by_configuration": True,
        "available": True,
        "unavailable_reasons": [],
    }


def test_unknown_feature_uses_the_core_not_found_envelope() -> None:
    response = TestClient(app).get("/api/v1/features/FX-F99")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "entity_not_found"
