from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.identity import User
from fashx.api.v1.onboarding import principal_user_uuid
from fashx.core.database import get_session_factory
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.revoke_consent import (
    RevokeConsentCommand,
    RevokeConsentUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import get_profile_uow
from fashx.profile.router import router as profile_router
from fashx.security.deps import Principal, get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from schemas.common.enums import DataType
from schemas.identity.consent import ConsentUpdate
from tests.conftest import make_token


@pytest.mark.asyncio
async def test_create_profile_binds_to_principal(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.1: Profile creation binds to authenticated user_id without creating duplicate users."""
    uow = ProfileUnitOfWork(session_factory)
    user_id = uuid4()

    # Pre-provision the user as if created during authentication resolve
    async with uow:
        user = User(id=user_id)
        uow.users.add(user)
        await uow.commit()

    use_case = CreateProfileUseCase(uow)
    cmd = CreateProfileCommand(
        user_id=user_id,
        height_cm=175,
        weight_kg=70,
        build="athletic",
        consents=[ConsentUpdate(data_type=DataType.MEASUREMENTS, granted=True)],
    )
    result = await use_case.execute(cmd)

    assert result.user_id == user_id
    assert result.height_cm == 175
    assert result.weight_kg == 70
    assert result.build == "athletic"

    # Verify no duplicate user was created
    async with uow:
        all_users = (await uow.session.scalars(select(User).where(User.id == user_id))).all()
        assert len(all_users) == 1
        body = await uow.body_profiles.get_by_user_id(user_id)
        assert body is not None
        assert body.height_cm == 175


def test_onboarding_principal_user_uuid_fail_closed() -> None:
    """MVP 2.2: Invalid principal user ID fails closed with 401 unauthorized."""
    invalid_principal = Principal(user_id="invalid-not-a-uuid", subject="sub-1", roles=frozenset(["user"]))

    with pytest.raises(ApiError) as exc_info:
        principal_user_uuid(invalid_principal)

    assert exc_info.value.status == 401
    assert exc_info.value.code == "unauthorized"

    # Valid UUID returns expected UUID
    valid_id = uuid4()
    valid_principal = Principal(user_id=str(valid_id), subject="sub-2", roles=frozenset(["user"]))
    assert principal_user_uuid(valid_principal) == valid_id


@pytest.mark.asyncio
async def test_consent_event_audit_logging(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.3: Consent grants, updates, and revocations append ConsentEvent audit records."""
    uow = ProfileUnitOfWork(session_factory)
    user_id = uuid4()

    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    # 1. Upsert consent and verify ConsentEvent
    async with uow:
        await uow.consents.upsert(
            user_id=user_id,
            data_type="measurements",
            granted=True,
            consent_version="2026.1",
            decision_source="settings_toggle",
        )
        await uow.commit()

    async with uow:
        events = await uow.consents.list_events_for_user(user_id)
        assert len(events) == 1
        assert events[0].data_type == "measurements"
        assert events[0].granted is True
        assert events[0].consent_version == "2026.1"
        assert events[0].decision_source == "settings_toggle"

    # 2. Revoke consent and verify revocation event
    tryon_uow = TryOnUnitOfWork(session_factory)
    revoke_uc = RevokeConsentUseCase(uow, tryon_uow)
    await revoke_uc.execute(RevokeConsentCommand(user_id=user_id, data_type="measurements"))

    async with uow:
        events = await uow.consents.list_events_for_user(user_id)
        assert len(events) == 2
        # Most recent event is the revocation
        assert events[0].granted is False
        assert events[0].data_type == "measurements"


@pytest.mark.asyncio
async def test_mobile_consent_creates_events(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.3: Mobile consent records both terms and body photo events atomically."""
    uow = ProfileUnitOfWork(session_factory)
    user_id = uuid4()

    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    async with uow:
        await uow.consents.record_mobile_consent(
            user_id=user_id,
            consent_version="2026.1",
            is_18_or_older=True,
            accepts_terms=True,
            accepts_body_photo=True,
        )
        await uow.commit()

    async with uow:
        events = await uow.consents.list_events_for_user(user_id)
        assert len(events) == 2
        event_types = {e.data_type for e in events}
        assert "terms_and_privacy" in event_types
        assert "body_photo" in event_types
        assert all(e.decision_source == "mobile_onboarding" for e in events)


def create_test_client(session_factory: async_sessionmaker[AsyncSession]) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.include_router(profile_router, prefix="/api/v1")
    return TestClient(app), repo


@pytest.mark.asyncio
async def test_get_profile_me_endpoint(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.4: GET /api/v1/profile/me retrieves the authenticated user's profile."""
    client, repo = create_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-me-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-me-test")

    # Set up user and body profile
    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id))
        await uow.body_profiles.upsert(user_id=user_id, height_cm=182, weight_kg=78, build="athletic")
        await uow.consents.upsert(user_id=user_id, data_type="measurements", granted=True)
        await uow.commit()

    resp = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["height_cm"] == 182
    assert data["weight_kg"] == 78
    assert data["build"] == "athletic"
    assert data["consents"].get("measurements") is True


@pytest.mark.asyncio
async def test_update_preferences_budget_validation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.4: PUT /api/v1/profile/preferences validates budget_min <= budget_max."""
    client, repo = create_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-pref-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-pref-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    # Invalid: budget_min > budget_max -> 422 Unprocessable Entity
    resp_invalid = client.put(
        "/api/v1/profile/preferences",
        json={"budget_min": 5000, "budget_max": 2000, "categories": ["tops"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_invalid.status_code == 422

    # Valid: budget_min <= budget_max -> 200 OK
    resp_valid = client.put(
        "/api/v1/profile/preferences",
        json={"budget_min": 1000, "budget_max": 3000, "categories": ["tops", "bottoms"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_valid.status_code == 200
    data = resp_valid.json()
    assert data["budget_min"] == 1000
    assert data["budget_max"] == 3000
    assert data["categories"] == ["tops", "bottoms"]


@pytest.mark.asyncio
async def test_record_measurement_omits_user_id(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.4: POST /api/v1/profile/measurements derives user_id from principal without requiring it in request body."""
    client, repo = create_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-meas-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-meas-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id))
        await uow.consents.upsert(user_id=user_id, data_type="measurements", granted=True)
        await uow.commit()

    # Request without user_id in payload
    resp = client.post(
        "/api/v1/profile/measurements",
        json={"measurement": "waist", "value": 81.5, "unit": "cm"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["measurement"] == "waist"
    assert data["value"] == 81.5

    # Request with mismatched user_id returns 403 Forbidden
    other_id = str(uuid4())
    resp_mismatch = client.post(
        "/api/v1/profile/measurements",
        json={"user_id": other_id, "measurement": "chest", "value": 100.0, "unit": "cm"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_mismatch.status_code == 403


@pytest.mark.asyncio
async def test_self_service_consents_endpoints(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """MVP 2.4: GET and PUT /api/v1/profile/consents work for self-service consent management."""
    client, repo = create_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-consent-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-consent-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id))
        await uow.commit()

    # PUT to grant consent
    resp_put = client.put(
        "/api/v1/profile/consents/marketing",
        json={"granted": True, "policy_url": "https://fashx.studio/privacy"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_put.status_code == 200
    data = resp_put.json()
    assert data["user_id"] == str(user_id)
    assert data["data_type"] == "marketing"
    assert data["granted"] is True

    # GET to list consents
    resp_get = client.get("/api/v1/profile/consents", headers={"Authorization": f"Bearer {token}"})
    assert resp_get.status_code == 200
    consents = resp_get.json()
    assert len(consents) >= 1
    assert any(c["data_type"] == "marketing" and c["granted"] is True for c in consents)
