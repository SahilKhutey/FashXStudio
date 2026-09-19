from api.app.main import app
from fastapi.testclient import TestClient


def test_liveness() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/system/health/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "AI Fashion Assistant API"
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Trace-ID"]


def test_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
