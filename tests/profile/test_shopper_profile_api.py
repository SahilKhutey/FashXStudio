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
async def test_get_profile_me_auto_creates_default(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-018: GET /api/v1/profile/me creates an empty default profile if none exists."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-auto-create")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-auto-create")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    resp = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["height_cm"] is None
    assert data["weight_kg"] is None
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_put_profile_me_create_or_replace(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-019: PUT /api/v1/profile/me creates or fully replaces profile."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-put-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-put-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    put_payload = {
        "height_cm": 178.5,
        "weight_kg": 72.0,
        "preferred_size_system": "IN",
        "preferred_fit": "REGULAR",
        "style_preferences": ["CASUAL", "FORMAL"],
        "preferred_colors": ["NAVY", "BLACK"],
        "product_categories": ["TOPS", "BOTTOMS"],
        "shopping_preferences": {
            "budget": {"min": 1000, "max": 4000, "currency": "INR"},
            "shopping_intents": ["WORKWEAR", "EVERYDAY_WEAR"],
            "preferred_brands": ["Zara", "FabIndia"],
        },
    }
    resp = client.put(
        "/api/v1/profile/me",
        json=put_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["height_cm"] == 178.5
    assert data["weight_kg"] == 72.0
    assert data["preferred_size_system"] == "IN"
    assert data["preferred_fit"] == "REGULAR"
    assert "CASUAL" in data["style_preferences"]
    assert float(data["shopping_preferences"]["budget"]["min"]) == 1000


@pytest.mark.asyncio
async def test_patch_profile_me_partial_update(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-020: PATCH /api/v1/profile/me partially updates fields while preserving others."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-patch-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-patch-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # Initial setup via PUT
    client.put(
        "/api/v1/profile/me",
        json={
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "preferred_fit": "REGULAR",
            "style_preferences": ["CASUAL"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Partial update via PATCH changing only preferred_fit
    resp_patch = client.patch(
        "/api/v1/profile/me",
        json={"preferred_fit": "SLIM"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_patch.status_code == 200
    data = resp_patch.json()
    assert data["preferred_fit"] == "SLIM"
    assert data["height_cm"] == 175.0  # Preserved
    assert data["weight_kg"] == 70.0  # Preserved
    assert data["style_preferences"] == ["CASUAL"]  # Preserved


@pytest.mark.asyncio
async def test_patch_profile_me_clearing_fields(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-021: PATCH /api/v1/profile/me can explicitly clear optional fields with null."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-clear-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-clear-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # Initial setup
    client.put(
        "/api/v1/profile/me",
        json={"height_cm": 180.0, "weight_kg": 75.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Clear weight_kg with null
    resp_clear = client.patch(
        "/api/v1/profile/me",
        json={"weight_kg": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_clear.status_code == 200
    data = resp_clear.json()
    assert data["weight_kg"] is None
    assert data["height_cm"] == 180.0


@pytest.mark.asyncio
async def test_optimistic_locking_conflict(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-022: Updating with an outdated expected_version returns HTTP 409 Conflict."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-conflict-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-conflict-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # Get initial profile
    resp_init = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    v1 = resp_init.json()["version"]

    # First update succeeds with expected_version = v1
    resp_up1 = client.patch(
        "/api/v1/profile/me",
        json={"height_cm": 170.0, "expected_version": v1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_up1.status_code == 200
    v2 = resp_up1.json()["version"]
    assert v2 > v1

    # Stale update with old expected_version v1 returns 409
    resp_stale = client.patch(
        "/api/v1/profile/me",
        json={"height_cm": 172.0, "expected_version": v1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_stale.status_code == 409


@pytest.mark.asyncio
async def test_feature_completeness_endpoint(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-023: GET /api/v1/profile/me/completeness evaluates readiness across features."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-complete-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-complete-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # Initial empty profile: low completeness
    resp_init = client.get(
        "/api/v1/profile/me/completeness", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_init.status_code == 200
    data_init = resp_init.json()
    assert "overall_percentage" in data_init
    assert data_init["features"]["advanced_vto"]["ready"] is False

    # Complete height and fit
    client.patch(
        "/api/v1/profile/me",
        json={
            "height_cm": 175.0,
            "preferred_fit": "REGULAR",
            "preferred_size_system": "IN",
            "product_categories": ["TOPS"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp_after = client.get(
        "/api/v1/profile/me/completeness", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_after.status_code == 200
    data_after = resp_after.json()
    assert data_after["features"]["advanced_vto"]["ready"] is True
    assert data_after["features"]["fit_recommendation"]["ready"] is True
    assert data_after["features"]["size_guidance"]["ready"] is True
    assert data_after["features"]["product_discovery"]["ready"] is True
    assert data_after["overall_percentage"] > data_init["overall_percentage"]


@pytest.mark.asyncio
async def test_category_sizes_endpoints(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """PROF-024: Category sizes GET and PUT endpoints."""
    client, repo = create_profile_test_client(session_factory)
    identity = await repo.resolve("fashx-test", "user-catsizes-test")
    user_id = UUID(identity.user_id)
    token = make_token(sub="user-catsizes-test")

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        uow.users.add(User(id=user_id, status=AccountStatus.ACTIVE.value))
        await uow.commit()

    # Set category sizes
    sizes_payload = [
        {"category_code": "TOPS", "size_system": "INTL", "size_label": "M"},
        {"category_code": "BOTTOMS", "size_system": "IN", "size_label": "32"},
    ]
    resp_put = client.put(
        "/api/v1/profile/me/category-sizes",
        json={"sizes": sizes_payload},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_put.status_code == 200
    data_put = resp_put.json()
    assert len(data_put) == 2

    # Get category sizes
    resp_get = client.get(
        "/api/v1/profile/me/category-sizes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert len(data_get) == 2
    cat_codes = {item["category_code"] for item in data_get}
    assert "TOPS" in cat_codes
    assert "BOTTOMS" in cat_codes
