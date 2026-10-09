import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fashx.api.v1.me import router as me_router
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


@pytest.fixture
def me_client():
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.include_router(me_router)
    return TestClient(app), repo


def test_get_me_unauthenticated(me_client):
    client, _ = me_client
    response = client.get("/me")
    assert response.status_code == 401


def test_get_me_authenticated(me_client):
    client, _ = me_client
    token = make_token(sub="test-user")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["roles"] == ["user"]
