from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from database.models.identity import User
from fashx.main import app
from fashx.recommendation.router import get_profile_uow
from fashx.security.deps import get_identity_repo
from tests.conftest import make_token


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_feed_api_contract_schema(api_client: TestClient) -> None:
    repo = app.dependency_overrides[get_identity_repo]()
    identity = await repo.resolve("fashx-test", "user-rc07-contract")
    user_id = identity.user_id
    token = make_token(sub="user-rc07-contract")
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure User record exists in DB
    profile_uow = app.dependency_overrides[get_profile_uow]()
    async with profile_uow:
        profile_uow.users.add(User(id=uuid.UUID(user_id)))
        await profile_uow.commit()

    resp = api_client.get("/api/v1/feed", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Schema structure verification
    assert "user_id" in data
    assert data["user_id"] == user_id
    assert "items" in data
    assert "total_candidates" in data
    assert "filtered_candidates" in data
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert "garment_id" in item
        assert "category" in item
        assert "price_minor" in item
        assert "relevance_score" in item
        assert 0.0 <= item["relevance_score"] <= 1.0
        assert "stylist_explanation" in item
        assert isinstance(item["stylist_explanation"], str)
        assert "reason_chips" in item
        assert isinstance(item["reason_chips"], list)
        assert len(item["reason_chips"]) <= 3
        assert "tryon_supported" in item
        assert isinstance(item["tryon_supported"], bool)
