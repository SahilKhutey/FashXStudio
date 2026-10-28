from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from database.models.commerce_feedback import DomainEvent
from database.models.pilot import PilotInvite
from fashx.api.v1.analytics import get_analytics_session_factory
from fashx.main import app
from fashx.pilot.router import hash_invite_code
from fashx.security.deps import get_identity_repo
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


@pytest.fixture(autouse=True)
def override_pilot_db_session():
    """Route pilot endpoint database access through test SQLite session."""
    session_factory = app.dependency_overrides[get_analytics_session_factory]()

    async def _sqlite_db_session():
        async with session_factory() as session:
            yield session

    with patch("fashx.pilot.router.get_db_session", _sqlite_db_session):
        yield


def test_pilot_invite_redemption_and_duplicate_join_guard() -> None:
    """Verify single-use invite redemption and rejection of repeat joins."""
    identity_repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo

    user_a_token = make_token(sub="pilot-alice")
    client_a = TestClient(app, headers={"Authorization": f"Bearer {user_a_token}"})

    code = "BETA-2026-TEST"
    code_h = hash_invite_code(code)

    session_factory = app.dependency_overrides[get_analytics_session_factory]()

    # Seed an invite in the SQLite test DB
    import asyncio

    async def _seed():
        async with session_factory() as session:
            invite = PilotInvite(
                code_hash=code_h,
                cohort="alpha",
                channel="community",
            )
            session.add(invite)
            await session.commit()

    asyncio.run(_seed())

    # 1. First redemption succeeds
    res1 = client_a.post("/api/v1/pilot/join", json={"code": code, "app_version": "1.0.0"})
    assert res1.status_code == 200
    assert res1.json()["cohort"] == "alpha"
    assert res1.json()["channel"] == "community"

    # 2. Second redemption with the SAME code fails with 404 (preventing enumeration)
    user_b_token = make_token(sub="pilot-bob")
    client_b = TestClient(app, headers={"Authorization": f"Bearer {user_b_token}"})
    res2 = client_b.post("/api/v1/pilot/join", json={"code": code, "app_version": "1.0.0"})
    assert res2.status_code == 404

    # 3. User A attempting to redeem ANOTHER code is rejected with 409 Conflict (duplicate enrollment guard)
    another_code = "BETA-2026-ANOTHER"
    another_h = hash_invite_code(another_code)

    async def _seed_another():
        async with session_factory() as session:
            invite2 = PilotInvite(
                code_hash=another_h,
                cohort="alpha",
                channel="referral",
            )
            session.add(invite2)
            await session.commit()

    asyncio.run(_seed_another())

    res3 = client_a.post("/api/v1/pilot/join", json={"code": another_code, "app_version": "1.0.0"})
    assert res3.status_code == 409
    assert "already joined" in res3.json()["detail"].lower()


def test_analytics_session_events_persisted_to_domain_events() -> None:
    """Verify that session events are saved to DomainEvent records in the database."""
    identity_repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo

    user_token = make_token(sub="analyst-user")
    client = TestClient(app, headers={"Authorization": f"Bearer {user_token}"})

    session_factory = app.dependency_overrides[get_analytics_session_factory]()
    garment_id = uuid4()

    batch = [
        {"event_type": "impression", "garment_id": str(garment_id), "session_id": "sess-123"},
        {"event_type": "click", "garment_id": str(garment_id), "session_id": "sess-123"},
        {"event_type": "tryon_submitted", "garment_id": str(garment_id), "session_id": "sess-123"},
        {"event_type": "retailer_opened", "garment_id": str(garment_id), "session_id": "sess-123"},
    ]

    res = client.post("/api/v1/analytics/session-events", json={"events": batch})
    assert res.status_code == 201
    assert res.json()["status"] == "recorded"
    assert res.json()["count"] == 4

    # Verify persisted in DomainEvent table
    import asyncio

    async def _verify():
        async with session_factory() as session:
            stmt = select(DomainEvent).where(DomainEvent.object_id == garment_id)
            records = (await session.execute(stmt)).scalars().all()
            assert len(records) >= 4
            event_types = {r.event_type for r in records}
            assert "session_impression" in event_types
            assert "session_click" in event_types
            assert "session_tryon_submitted" in event_types
            assert "session_retailer_opened" in event_types

    asyncio.run(_verify())


def test_pilot_feedback_submission_and_storage() -> None:
    """Verify qualitative feedback submission via POST /api/v1/pilot/feedback."""
    identity_repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo

    user_token = make_token(sub="tester-feedback")
    client = TestClient(app, headers={"Authorization": f"Bearer {user_token}"})

    payload = {
        "kind": "idea",
        "message": "Add a split-screen slider for virtual try-on comparison.",
        "context": {"screen": "tryon_preview", "app_version": "1.0.0-beta"},
    }

    res = client.post("/api/v1/pilot/feedback", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"


def test_pilot_survey_submission_and_duplicate_conflict() -> None:
    """Verify survey validation and 409 conflict when resubmitting the same survey."""
    identity_repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo

    user_token = make_token(sub="tester-survey")
    client = TestClient(app, headers={"Authorization": f"Bearer {user_token}"})

    payload = {
        "survey_key": "tryon_first",
        "answers": {
            "looked_like_me": 4,
            "trust_for_buying": 4,
            "comment": "Looks convincing on upper body.",
        },
    }

    # 1. First submission succeeds
    res1 = client.post("/api/v1/pilot/survey", json=payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "recorded"

    # 2. Duplicate submission triggers 409 Conflict
    res2 = client.post("/api/v1/pilot/survey", json=payload)
    assert res2.status_code == 409
    assert "already been submitted" in res2.json()["detail"].lower()
