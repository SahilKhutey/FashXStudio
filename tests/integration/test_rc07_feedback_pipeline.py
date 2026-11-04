from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from fashx.main import app as main_app
from fashx.security.deps import get_identity_repo
from tests.conftest import make_token


@pytest.fixture
def api_client():
    return TestClient(main_app)


@pytest.mark.asyncio
async def test_record_feed_signals_with_auth(api_client: TestClient) -> None:
    repo = main_app.dependency_overrides[get_identity_repo]()
    identity_a = await repo.resolve("fashx-test", "user-rc07-a")
    user_a_id = identity_a.user_id
    token_a = make_token(sub="user-rc07-a")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    garment_id = str(uuid.uuid4())

    for action in ("like", "hide", "not_interested"):
        resp = api_client.post(
            "/api/v1/feed/signals",
            json={"garment_id": garment_id, "action": action},
            headers=headers_a,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "recorded"
        assert data["user_id"] == user_a_id
        assert data["garment_id"] == garment_id
        assert data["action"] == action

    # Invalid action is rejected by validation schema
    bad_resp = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": garment_id, "action": "invalid_action"},
        headers=headers_a,
    )
    assert bad_resp.status_code in (400, 422)


def test_feed_signals_require_authentication(api_client: TestClient) -> None:
    garment_id = str(uuid.uuid4())
    resp = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": garment_id, "action": "like"},
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_user_isolation_on_feed_signals(api_client: TestClient) -> None:
    repo = main_app.dependency_overrides[get_identity_repo]()
    identity_a = await repo.resolve("fashx-test", "user-rc07-iso-a")
    identity_b = await repo.resolve("fashx-test", "user-rc07-iso-b")
    user_a_id = identity_a.user_id
    user_b_id = identity_b.user_id

    assert user_a_id != user_b_id

    token_a = make_token(sub="user-rc07-iso-a")
    token_b = make_token(sub="user-rc07-iso-b")

    garment_id = str(uuid.uuid4())

    # User A records 'like'
    resp_a = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": garment_id, "action": "like"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 201
    assert resp_a.json()["user_id"] == user_a_id

    # User B records 'hide' on the same garment
    resp_b = api_client.post(
        "/api/v1/feed/signals",
        json={"garment_id": garment_id, "action": "hide"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 201
    assert resp_b.json()["user_id"] == user_b_id
