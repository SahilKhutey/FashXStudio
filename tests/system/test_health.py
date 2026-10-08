from fastapi.testclient import TestClient

from fashx.main import app
from fashx.core.bootstrap import register_core_services
from fashx.core.runtime import CoreRuntime
from fashx.core.version import CORE_API_VERSION, CORE_VERSION, PRODUCT_NAME
from fashx.integration.health import evaluate_system_health

client = TestClient(app)


def test_evaluate_system_health():
    runtime = CoreRuntime()
    register_core_services(runtime)

    health = evaluate_system_health(runtime)
    assert health.status == "healthy"
    assert len(health.components) > 0
    for comp in health.components:
        assert comp.status == "healthy"


def test_evaluate_system_health_degraded():
    empty_runtime = CoreRuntime()
    health = evaluate_system_health(empty_runtime)
    assert health.status == "degraded"


def test_system_health_endpoint():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["product"] == PRODUCT_NAME
    assert data["core_version"] == CORE_VERSION
    assert data["api_version"] == CORE_API_VERSION
    assert "details" in data
