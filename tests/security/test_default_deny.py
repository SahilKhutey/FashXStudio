import pytest
from fastapi.testclient import TestClient

from fashx.main import app
from fashx.security.deps import get_identity_repo
from fashx.security.identity import InMemoryIdentityRepo
from fashx.security.public_routes import is_public_path
from scripts.security.route_inventory import extract_routes
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
    for path in ["/", "/api/v1/system/health/live", "/api/v1/system/health/ready", "/api/v1/system/health", "/api/v1/system/ready"]:
        res = anon_client.get(path)
        assert res.status_code == 200, f"Expected 200 for public route {path}, got {res.status_code}"


def test_protected_routes_deny_anonymous(auth_test_context):
    anon_client, _, _ = auth_test_context
    routes = extract_routes(app)

    tested = 0
    for path, route in routes:
        # Skip public routes, capability endpoints, and unit test fixtures
        if is_public_path(path) or "/test-errors" in path or path.startswith("/dev-files"):
            continue

        method = next(iter(route.methods - {"HEAD", "OPTIONS"}))
        # Call route with dummy or empty payload
        response = anon_client.request(method, path)
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated request to {method} {path}, got {response.status_code}"
        )
        assert response.json()["title"] == "unauthorized"
        tested += 1

    assert tested > 10, f"Expected to test numerous protected routes, only tested {tested}"


def test_dev_files_denies_unsigned(auth_test_context):
    anon_client, _, _ = auth_test_context
    res = anon_client.get("/dev-files/some/secret/photo.jpg")
    assert res.status_code == 403


def test_protected_routes_deny_invalid_token(auth_test_context):
    anon_client, _, _ = auth_test_context
    client_bad = TestClient(app, headers={"Authorization": "Bearer invalid.token.payload"})
    res = client_bad.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["title"] == "unauthorized"


def test_catalog_admin_role_enforcement(auth_test_context):
    _, user_client, repo = auth_test_context
    # Normal user (role: user) attempts to access catalog endpoint
    res = user_client.get("/api/v1/catalog/quality-audit")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"
