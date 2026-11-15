from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.identity import User
from fashx.account.schemas import AccountStatus
from fashx.core.database import get_session_factory
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import get_profile_uow
from fashx.profile.router import router as profile_router
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from tests.conftest import make_token


def create_profile_test_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.include_router(profile_router, prefix="/api/v1")
    return TestClient(app), repo


@pytest.mark.asyncio
async def test_shopper_profile_ownership_isolation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-012: User A and User B profiles are strictly isolated."""
    client, repo = create_profile_test_client(session_factory)

    # Create User A
    id_a = await repo.resolve("fashx-test", "user-a")
    user_a_id = UUID(id_a.user_id)
    token_a = make_token(sub="user-a")

    # Create User B
    id_b = await repo.resolve("fashx-test", "user-b")
    user_b_id = UUID(id_b.user_id)
    token_b = make_token(sub="user-b")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_a_id, status=AccountStatus.ACTIVE.value))
        uow.users.add(User(id=user_b_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # User A sets their profile
    resp_a_put = client.put(
        "/api/v1/profile/me",
        json={"height_cm": 180.0, "preferred_fit": "SLIM"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a_put.status_code == 200
    assert resp_a_put.json()["height_cm"] == 180.0

    # User B sets their profile
    resp_b_put = client.put(
        "/api/v1/profile/me",
        json={"height_cm": 165.0, "preferred_fit": "RELAXED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b_put.status_code == 200
    assert resp_b_put.json()["height_cm"] == 165.0

    # User A gets profile: must only see User A's data
    resp_a_get = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a_get.status_code == 200
    assert resp_a_get.json()["user_id"] == str(user_a_id)
    assert resp_a_get.json()["height_cm"] == 180.0
    assert resp_a_get.json()["preferred_fit"] == "SLIM"

    # User B gets profile: must only see User B's data
    resp_b_get = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b_get.status_code == 200
    assert resp_b_get.json()["user_id"] == str(user_b_id)
    assert resp_b_get.json()["height_cm"] == 165.0
    assert resp_b_get.json()["preferred_fit"] == "RELAXED"


@pytest.mark.asyncio
async def test_disabled_account_blocked(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-014: Disabled account cannot access profile endpoints."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "disabled-user")
    user_id = UUID(identity.user_id)
    token = make_token(sub="disabled-user")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.DISABLED.value))
        await uow.commit()

    resp = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "disabled" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deletion_pending_account_blocked(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-015: Deletion pending account cannot access profile endpoints."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "pending-delete-user")
    user_id = UUID(identity.user_id)
    token = make_token(sub="pending-delete-user")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.DELETION_PENDING.value))
        await uow.commit()

    resp = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "deletion" in resp.json()["detail"].lower()


def test_unauthenticated_request_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-016: Requests without valid Authorization header fail closed with 401."""
    client, _ = create_profile_test_client(session_factory)
    resp = client.get("/api/v1/profile/me", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401
