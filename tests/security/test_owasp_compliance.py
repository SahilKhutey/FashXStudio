
import pytest
from fastapi.testclient import TestClient

from fashx.ingest.safe_http import Reject, assert_public_https
from fashx.main import app
from fashx.security.deps import get_principal


def test_ssrf_rejects_non_https():
    with pytest.raises(Reject) as exc:
        assert_public_https("http://example.com/feed.json")
    assert exc.value.code == "non_https_url"


def test_ssrf_rejects_loopback_and_metadata():
    # 127.0.0.1 loopback
    with pytest.raises(Reject) as exc:
        assert_public_https("https://127.0.0.1/admin")
    assert exc.value.code == "private_address"

    # AWS metadata link-local 169.254.169.254
    with pytest.raises(Reject) as exc:
        assert_public_https("https://169.254.169.254/latest/meta-data")
    assert exc.value.code == "private_address"

    # RFC 1918 private subnet 10.0.0.1
    with pytest.raises(Reject) as exc:
        assert_public_https("https://10.0.0.1/secrets")
    assert exc.value.code == "private_address"


def test_function_level_auth_blocks_regular_user_from_admin():
    from fashx.security.deps import Principal

    regular_principal = Principal(
        user_id="usr_normal_001",
        subject="normal@fashx.studio",
        roles=frozenset(["user"]),
    )

    app.dependency_overrides[get_principal] = lambda: regular_principal
    client = TestClient(app)

    try:
        # User attempts to hit admin feature flags
        resp = client.post(
            "/api/v1/admin/feature-flags",
            json={"name": "maintenance_mode", "enabled": True, "reason": "Hacking"},
        )
        assert resp.status_code == 403
        assert resp.json().get("title") == "forbidden"

        # User attempts to hit catalog management
        resp_cat = client.get("/api/v1/catalog/quality-audit")
        assert resp_cat.status_code == 403
    finally:
        app.dependency_overrides.pop(get_principal, None)


def test_bola_user_isolation_on_me_endpoint():
    from fashx.security.deps import Principal

    user_a = Principal(
        user_id="usr_alice_001",
        subject="alice@fashx.studio",
        roles=frozenset(["user"]),
    )

    app.dependency_overrides[get_principal] = lambda: user_a
    client = TestClient(app)

    try:
        # Alice requests her own data
        resp = client.get("/api/v1/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("user_id") == "usr_alice_001"
    finally:
        app.dependency_overrides.pop(get_principal, None)
