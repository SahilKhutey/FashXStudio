from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from database.models.catalog import CanonicalGarment
from database.models.identity import User
from fashx.api.v1.me import get_profile_uow
from fashx.catalog.router import get_catalog_uow
from fashx.main import app


@pytest.mark.asyncio
async def test_feed_endpoint_pagination_and_fields() -> None:
    client = TestClient(app)
    me_res = client.get("/api/v1/me")
    assert me_res.status_code == 200
    user_id = UUID(me_res.json()["user_id"])

    profile_uow = app.dependency_overrides[get_profile_uow]()
    async with profile_uow:
        existing = await profile_uow.users.get_by_id(user_id)
        if not existing:
            profile_uow.users.add(User(id=user_id))
            await profile_uow.commit()

    res = client.get("/api/v1/feed?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total_candidates" in data
    assert "filtered_candidates" in data
    assert "next_cursor" in data
    assert "empty_reason" in data
    assert "relaxed" in data


def test_analytics_session_events_batch() -> None:
    client = TestClient(app)
    events = [
        {"event_type": "impression", "garment_id": "00000000-0000-0000-0000-000000000001"},
        {"event_type": "impression", "garment_id": "00000000-0000-0000-0000-000000000002"},
    ]
    res = client.post("/api/v1/analytics/session-events", json={"events": events})
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "recorded"
    assert data["count"] == 2


@pytest.mark.asyncio
async def test_tryon_jobs_rejects_unsupported_garment_with_422() -> None:
    client = TestClient(app)
    me_res = client.get("/api/v1/me")
    assert me_res.status_code == 200
    user_id = UUID(me_res.json()["user_id"])

    profile_uow = app.dependency_overrides[get_profile_uow]()
    async with profile_uow:
        existing = await profile_uow.users.get_by_id(user_id)
        if not existing:
            profile_uow.users.add(User(id=user_id))
            await profile_uow.commit()

    unsupported_id = uuid4()
    catalog_uow = app.dependency_overrides[get_catalog_uow]()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=unsupported_id,
            category="accessories",
            subcategory="scarf",
            gender="unisex",
            price_minor=49900,
            active=True,
            tryon_supported=False,
            display_name="Silk Scarf",
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    res = client.post(
        "/api/v1/tryon/jobs",
        json={"garment_id": str(unsupported_id)},
        headers={"Idempotency-Key": f"test-idemp-{uuid4()}"},
    )
    assert res.status_code == 422
    assert "not supported" in str(res.json()).lower()
