from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from fashx.core.settings import Settings
from fashx.main import app, create_app
from fashx.security.deps import get_identity_repo
from fashx.security.identity import InMemoryIdentityRepo
from fashx.security.public_routes import is_public_path
from tests.conftest import make_token


@pytest.fixture
def auth_test_context():
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    anon_client = TestClient(app)
    user_token = make_token(sub="alice")
    user_client = TestClient(app, headers={"Authorization": f"Bearer {user_token}"})
    return anon_client, user_client, repo


def test_public_routes_allowlist(auth_test_context):
    anon_client, _, _ = auth_test_context
    for path in [
        "/",
        "/api/v1/system/health/live",
        "/healthz/live",
        "/api/v1/system/health",
        "/api/v1/system/ready",
        "/api/v1/config",
    ]:
        res = anon_client.get(path)
        assert res.status_code == 200, f"Expected 200 for public route {path}, got {res.status_code}"

    # Readiness may return 200 or 503 depending on database availability in test
    for path in ["/api/v1/system/health/ready", "/healthz/ready"]:
        res = anon_client.get(path)
        assert res.status_code in (200, 503), f"Expected 200 or 503 for readiness {path}, got {res.status_code}"

    config_res = anon_client.get("/api/v1/config")
    cfg = config_res.json()
    assert "min_app_version" in cfg
    assert "maintenance" in cfg
    assert "tryon_supported_categories" in cfg
    assert "flags" in cfg


def test_protected_routes_deny_anonymous_openapi_coverage(auth_test_context):
    anon_client, _, _ = auth_test_context
    paths = app.openapi()["paths"]

    assert len(paths) >= 100, f"Expected at least 100 OpenAPI paths, found {len(paths)}"

    tested = 0
    non_401 = []

    for raw_path, path_item in paths.items():
        if is_public_path(raw_path) or raw_path.startswith("/dev-files"):
            continue

        resolved_path = re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", raw_path)

        for method in path_item.keys():
            m = method.upper()
            if m in ("OPTIONS", "HEAD"):
                continue

            res = anon_client.request(m, resolved_path)
            if res.status_code != 401:
                non_401.append((m, raw_path, res.status_code))
            else:
                assert res.json().get("title") == "unauthorized" or "detail" in res.json()
            tested += 1

    assert non_401 == [], f"Non-public routes did not return 401: {non_401}"
    assert tested >= 100, f"Expected >= 100 tested protected endpoints, tested {tested}"


def test_unauthenticated_non_401_routes_match_public_allowlist(auth_test_context):
    anon_client, _, _ = auth_test_context
    paths = app.openapi()["paths"]

    for raw_path, path_item in paths.items():
        resolved_path = re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", raw_path)
        for method in path_item.keys():
            m = method.upper()
            if m in ("OPTIONS", "HEAD"):
                continue
            res = anon_client.request(m, resolved_path)
            if res.status_code != 401:
                assert is_public_path(raw_path) or raw_path.startswith("/dev-files"), (
                    f"Route {m} {raw_path} returned {res.status_code} but is not marked public"
                )


def test_docs_and_openapi_gated_in_production():
    prod_settings = Settings(
        env="prod",
        repo_backend="sql",
        storage_backend="s3",
        enable_b2b=False,
        enable_frozen=False,
        s3_bucket="fashx-prod-bucket",
        s3_use_iam_role=True,
        auth_mode="jwks",
        auth_jwks_url="https://auth.example.com/.well-known/jwks.json",
        tryon_provider="fashn_api",
        fashn_api_key="test-key-mock",
        privacy_url="https://fashx.com/privacy",
        terms_url="https://fashx.com/terms",
    )
    prod_app = create_app(prod_settings)
    client = TestClient(prod_app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_protected_routes_deny_invalid_token(auth_test_context):
    anon_client, _, _ = auth_test_context
    client_bad = TestClient(app, headers={"Authorization": "Bearer invalid.token.payload"})
    res = client_bad.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["title"] == "unauthorized"


def test_catalog_admin_role_enforcement(auth_test_context):
    _, user_client, repo = auth_test_context
    res = user_client.get("/api/v1/catalog/quality-audit")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"


def test_catalog_admin_garment_routes_deny_normal_user(auth_test_context):
    _, user_client, _ = auth_test_context
    dummy_uuid = "00000000-0000-0000-0000-000000000000"
    for method, path, payload in [
        ("GET", f"/api/v1/catalog/garments/{dummy_uuid}", None),
        ("POST", f"/api/v1/catalog/garments/{dummy_uuid}/enrich", {}),
        ("POST", f"/api/v1/catalog/garments/{dummy_uuid}/size-charts", {"raw_text": "S M L"}),
        ("POST", "/api/v1/catalog/products", {}),
        ("GET", "/api/v1/catalog/quality-audit", None),
    ]:
        res = user_client.request(method, path, json=payload if payload is not None else None)
        assert res.status_code == 403, (
            f"Expected 403 for normal user on admin route {method} {path}, got {res.status_code}"
        )
        assert res.json()["title"] == "forbidden"
