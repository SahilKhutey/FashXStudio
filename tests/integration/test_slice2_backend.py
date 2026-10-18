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


def test_session_events_enforces_forbid_extra_and_max_batch_cap() -> None:
    client = TestClient(app)

    # 1. Reject batch exceeding 100 events
    too_many = [
        {"event_type": "impression", "garment_id": str(uuid4())} for _ in range(101)
    ]
    res_too_many = client.post("/api/v1/analytics/session-events", json={"events": too_many})
    assert res_too_many.status_code in (400, 422)

    # 2. Reject unknown/extra fields (extra="forbid")
    res_extra = client.post(
        "/api/v1/analytics/session-events",
        json={"events": [{"event_type": "impression", "unknown_field": "disallowed"}]},
    )
    assert res_extra.status_code in (400, 422)

    # 3. Valid batch within cap succeeds
    valid_batch = [
        {"event_type": "impression", "garment_id": str(uuid4())} for _ in range(5)
    ]
    res_valid = client.post("/api/v1/analytics/session-events", json={"events": valid_batch})
    assert res_valid.status_code == 201
    assert res_valid.json()["count"] == 5


@pytest.mark.asyncio
async def test_cross_user_tryon_isolation() -> None:
    from database.models.tryon import TryOnJob
    from fashx.security.deps import Principal, get_principal
    from fashx.tryon.router import get_tryon_uow

    alice_id = uuid4()
    bob_id = uuid4()

    # Create Alice's job in DB
    tryon_uow = app.dependency_overrides[get_tryon_uow]()
    job_id = uuid4()
    garment_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=alice_id,
            garment_id=garment_id,
            profile_photo_id=uuid4(),
            idempotency_key=f"alice-{uuid4()}",
            artifact_key=f"art-{uuid4()}",
            status="completed",
            model_version="v1",
            pipeline_version="v1",
            provider="mock",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    # Authenticated as Bob
    bob_principal = Principal(user_id=str(bob_id), subject="bob", roles=frozenset(["user"]))
    app.dependency_overrides[get_principal] = lambda: bob_principal

    try:
        client = TestClient(app)

        # 1. Bob's job listing does NOT contain Alice's job
        list_res = client.get("/api/v1/tryon/jobs")
        assert list_res.status_code == 200
        jobs = list_res.json()
        assert not any(j["job_id"] == str(job_id) for j in jobs)

        # 2. Bob cannot get Alice's job status (404 EntityNotFoundError)
        detail_res = client.get(f"/api/v1/tryon/jobs/{job_id}")
        assert detail_res.status_code == 404

        # 3. Bob cannot submit feedback spoofing Alice's user_id (403 Forbidden)
        fb_res = client.post(
            "/api/v1/feedback/tryon",
            json={
                "user_id": str(alice_id),
                "tryon_job_id": str(job_id),
                "visual_accuracy": "accurate",
            },
        )
        assert fb_res.status_code == 403
    finally:
        app.dependency_overrides.pop(get_principal, None)

