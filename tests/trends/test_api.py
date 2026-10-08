from fastapi.testclient import TestClient

from fashx.core.bootstrap import register_core_services
from fashx.core.runtime import get_core_runtime
from app.main import app

client = TestClient(app)


def test_trend_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/trends" in paths
    assert "/api/v1/trends/observations" in paths
    assert "/api/v1/trends/{trend_id}" in paths
    assert "/api/v1/trends/{trend_id}/activate" in paths


def test_create_trend_observation_api():
    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    response = client.post(
        "/api/v1/trends/observations",
        json={
            "topic": "oversized jacket",
            "trend_type": "style",
            "signal_type": "search_volume",
            "source": "search",
            "value": "9200",
            "region": "IN",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "oversized jacket"
    assert data["source"] == "search"
    assert data["signal_type"] == "search_volume"
    assert data["region"] == "IN"


def test_create_and_get_trend_api():
    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    create_res = client.post(
        "/api/v1/trends",
        json={
            "topic": "quiet luxury",
            "trend_type": "style",
            "region": "IN",
            "strength": 0.85,
            "momentum": 0.35,
            "confidence": 0.90,
        },
    )
    assert create_res.status_code == 200
    trend_data = create_res.json()
    trend_id = trend_data["id"]
    assert trend_data["topic"] == "quiet luxury"
    assert trend_data["strength"] == 0.85
    assert trend_data["status"] == "draft"

    get_res = client.get(f"/api/v1/trends/{trend_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == trend_id


def test_activate_and_list_trends_api():
    runtime = get_core_runtime()
    register_core_services(runtime)
    app.state.core_runtime = runtime

    create_res = client.post(
        "/api/v1/trends",
        json={
            "topic": "baggy denim",
            "trend_type": "material",
            "region": "IN",
            "strength": 0.78,
            "momentum": 0.20,
            "confidence": 0.80,
        },
    )
    trend_id = create_res.json()["id"]

    # Before activation, list_active should not include this draft trend
    list_res1 = client.get("/api/v1/trends?trend_type=material")
    assert list_res1.status_code == 200
    ids_before = [t["id"] for t in list_res1.json()]
    assert trend_id not in ids_before

    # Activate
    activate_res = client.post(f"/api/v1/trends/{trend_id}/activate")
    assert activate_res.status_code == 200
    assert activate_res.json()["status"] == "active"

    # After activation, list_active should include it
    list_res2 = client.get("/api/v1/trends?region=IN&trend_type=material")
    assert list_res2.status_code == 200
    ids_after = [t["id"] for t in list_res2.json()]
    assert trend_id in ids_after
