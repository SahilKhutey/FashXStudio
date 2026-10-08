from fastapi.testclient import TestClient

from fashx.main import app

client = TestClient(app)


def test_system_ready_endpoint():
    response = client.get("/api/v1/system/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
