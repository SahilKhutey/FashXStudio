from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from fashx.main import create_app


def test_liveness_endpoint_returns_200():
    app = create_app()
    client = TestClient(app)

    response = client.get("/healthz/live")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "password" not in response.text
    assert "postgresql://" not in response.text
    assert "redis://" not in response.text


def test_system_liveness_endpoint_returns_200():
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/system/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_readiness_endpoint_healthy():
    app = create_app()
    client = TestClient(app)

    with (
        patch("fashx.health.router.check_database", AsyncMock(return_value=True)),
        patch("fashx.health.router.check_redis_dependency", AsyncMock(return_value=True)),
        patch("fashx.health.router.check_jwks_dependency", AsyncMock(return_value=True)),
    ):
        response = client.get("/healthz/ready")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("database") == "ok"


def test_readiness_endpoint_fails_when_database_down():
    app = create_app()
    client = TestClient(app)

    with (
        patch("fashx.health.router.check_database", AsyncMock(return_value=False)),
        patch("fashx.health.router.check_redis_dependency", AsyncMock(return_value=True)),
        patch("fashx.health.router.check_jwks_dependency", AsyncMock(return_value=True)),
        patch("fashx.health.router.get_settings") as mock_settings,
    ):
        mock_s = mock_settings.return_value
        mock_s.is_production = True
        mock_s.app_name = "fashx"
        mock_s.app_version = "0.2.0"
        mock_s.env = "staging"
        response = client.get("/healthz/ready")
        assert response.status_code == 503
        data = response.json()
        assert data.get("status") == "degraded"
        assert data.get("database") == "error"


def test_system_readiness_endpoint_healthy():
    app = create_app()
    client = TestClient(app)

    with (
        patch("fashx.health.router.check_database", AsyncMock(return_value=True)),
        patch("fashx.health.router.check_redis_dependency", AsyncMock(return_value=True)),
        patch("fashx.health.router.check_jwks_dependency", AsyncMock(return_value=True)),
    ):
        response = client.get("/api/v1/system/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
