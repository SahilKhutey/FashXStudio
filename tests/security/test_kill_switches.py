import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from fashx.core.flags import (
    MAINTENANCE_MODE,
    TRYON_ENABLED,
    clear_flag_cache,
    is_flag_enabled,
    set_flag,
)
from fashx.main import app
from fashx.security.deps import get_principal
from fashx.security.tokens import Claims


@pytest.fixture(autouse=True)
def reset_flags():
    clear_flag_cache()
    yield
    clear_flag_cache()


@pytest.mark.asyncio
async def test_flag_lookup_cache_and_default():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = False
    mock_session.execute.return_value = mock_result

    # First lookup queries session
    val1 = await is_flag_enabled("custom_feature", default=True, session=mock_session)
    assert val1 is False
    assert mock_session.execute.call_count == 1

    # Second lookup hits 30s in-memory cache without calling session again
    val2 = await is_flag_enabled("custom_feature", default=True, session=mock_session)
    assert val2 is False
    assert mock_session.execute.call_count == 1


@pytest.mark.asyncio
async def test_set_flag_invalidates_cache_and_updates():
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.rowcount = 1
    mock_session.execute.return_value = mock_res

    await set_flag(
        flag_name="tryon_enabled",
        enabled=False,
        updated_by="admin_user_01",
        reason="Vendor provider outage containment",
        session=mock_session,
    )

    # Immediately reflected in cache
    val = await is_flag_enabled("tryon_enabled")
    assert val is False


def test_admin_feature_flags_endpoint_requires_admin_role():
    client = TestClient(app)

    # Calling without auth -> 401
    resp = client.post(
        "/api/v1/admin/feature-flags",
        json={"name": "tryon_enabled", "enabled": False, "reason": "Testing"},
    )
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_admin_feature_flags_endpoint_success_with_admin(monkeypatch):
    from unittest.mock import AsyncMock
    import fashx.admin.router as admin_mod
    from fashx.security.deps import Principal

    mock_set = AsyncMock()
    monkeypatch.setattr(admin_mod, "set_flag", mock_set)

    admin_principal = Principal(
        user_id="usr_admin_001",
        subject="admin@fashx.studio",
        roles=frozenset(["admin"]),
    )

    app.dependency_overrides[get_principal] = lambda: admin_principal
    client = TestClient(app)

    try:
        resp = client.post(
            "/api/v1/admin/feature-flags",
            json={"name": "tryon_enabled", "enabled": False, "reason": "Emergency testing"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "tryon_enabled"
        assert data["enabled"] is False
        assert data["status"] == "updated"
        mock_set.assert_called_once_with(
            flag_name="tryon_enabled",
            enabled=False,
            updated_by="usr_admin_001",
            reason="Emergency testing",
        )
    finally:
        app.dependency_overrides.pop(get_principal, None)


def test_maintenance_mode_middleware():
    from fashx.core.flags import _FLAG_CACHE
    import time

    # Simulate maintenance_mode active in cache
    _FLAG_CACHE[MAINTENANCE_MODE] = (True, time.monotonic())

    client = TestClient(app)
    try:
        resp = client.get("/api/v1/config")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert resp.headers.get("Retry-After") == "60"

        # Admin and health paths remain accessible
        resp_health = client.get("/healthz/live")
        assert resp_health.status_code == status.HTTP_200_OK
    finally:
        clear_flag_cache()
