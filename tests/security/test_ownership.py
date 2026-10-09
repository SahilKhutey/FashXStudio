import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from fashx.main import app
from fashx.security.deps import get_identity_repo
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.router import get_tryon_uow
from tests.conftest import make_token


@pytest.fixture
def ownership_context():
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo

    # Resolve deterministic user IDs
    user_a = asyncio.run(repo.resolve("fashx-test", "user-a"))
    user_b = asyncio.run(repo.resolve("fashx-test", "user-b"))
    admin = asyncio.run(repo.resolve("fashx-test", "admin-user"))
    asyncio.run(repo.set_role("fashx-test", "admin-user", "admin"))

    token_a = make_token(sub="user-a")
    token_b = make_token(sub="user-b")
    token_admin = make_token(sub="admin-user")

    client_a = TestClient(app, headers={"Authorization": f"Bearer {token_a}"})
    client_b = TestClient(app, headers={"Authorization": f"Bearer {token_b}"})
    client_admin = TestClient(app, headers={"Authorization": f"Bearer {token_admin}"})

    return {
        "client_a": client_a,
        "client_b": client_b,
        "client_admin": client_admin,
        "user_a_id": user_a.user_id,
        "user_b_id": user_b.user_id,
        "admin_id": admin.user_id,
    }


def test_user_cannot_access_other_user_profile(ownership_context):
    client_a = ownership_context["client_a"]
    user_b_id = ownership_context["user_b_id"]

    # Derived profile
    res = client_a.get(f"/api/v1/profile/{user_b_id}/derived")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"

    # Photos upload
    res = client_a.post(
        f"/api/v1/profile/{user_b_id}/photos",
        json={"photo_type": "tryon_reference", "photo_b64": "dGVzdA=="},
    )
    assert res.status_code == 403

    # Preferences update
    res = client_a.put(
        f"/api/v1/profile/{user_b_id}/preferences",
        json={"colors_favored": ["blue"]},
    )
    assert res.status_code == 403

    # Consent revocation
    res = client_a.post(
        f"/api/v1/profile/{user_b_id}/consent/revoke",
        json={"data_type": "body_photo"},
    )
    assert res.status_code == 403


def test_user_cannot_access_other_user_recommendations(ownership_context):
    client_a = ownership_context["client_a"]
    user_b_id = ownership_context["user_b_id"]

    res = client_a.get(f"/api/v1/recommendations/feed/{user_b_id}")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"

    res = client_a.post(
        "/api/v1/recommendations/exclusions",
        json={"user_id": user_b_id},
    )
    assert res.status_code == 403


def test_user_cannot_access_other_user_wardrobe(ownership_context):
    client_a = ownership_context["client_a"]
    user_b_id = ownership_context["user_b_id"]

    res = client_a.get(f"/api/v1/wardrobe/users/{user_b_id}")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"

    item_id = uuid4()
    res = client_a.delete(f"/api/v1/wardrobe/items/{item_id}?user_id={user_b_id}")
    assert res.status_code == 403

    res = client_a.post(
        "/api/v1/wardrobe/items",
        json={"user_id": user_b_id, "garment_id": str(uuid4())},
    )
    assert res.status_code == 403


def test_user_cannot_access_other_user_tryon_jobs(ownership_context):
    client_a = ownership_context["client_a"]
    user_b_id = ownership_context["user_b_id"]

    # Submit job for user b
    res = client_a.post(
        "/api/v1/tryon/jobs",
        json={"user_id": user_b_id, "garment_id": str(uuid4())},
        headers={"Idempotency-Key": "key-123"},
    )
    assert res.status_code == 403


def test_other_user_job_status_returns_not_found(ownership_context):
    client_a = ownership_context["client_a"]
    user_b_id = ownership_context["user_b_id"]
    job_id = uuid4()

    # Mock TryOnUnitOfWork returning a job belonging to user_b
    mock_uow = MagicMock()
    mock_job = MagicMock()
    mock_job.id = job_id
    mock_job.user_id = user_b_id
    mock_job.status = "queued"
    mock_job.artifact_key = "artifacts/123"
    mock_job.failure_reason = None
    mock_job.model_version = "v1"
    mock_job.pipeline_version = "v1"

    mock_uow.jobs.get_by_id = AsyncMock(return_value=mock_job)
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    app.dependency_overrides[get_tryon_uow] = lambda: mock_uow
    try:
        res = client_a.get(f"/api/v1/tryon/jobs/{job_id}")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.pop(get_tryon_uow, None)


def test_admin_cannot_access_user_biometrics_or_photos(ownership_context):
    client_admin = ownership_context["client_admin"]
    user_b_id = ownership_context["user_b_id"]

    # Admin attempting to view user photos/profile is denied
    res = client_admin.get(f"/api/v1/profile/{user_b_id}/derived")
    assert res.status_code == 403
    assert res.json()["title"] == "forbidden"

    res = client_admin.post(
        f"/api/v1/profile/{user_b_id}/photos",
        json={"photo_type": "tryon_reference", "photo_b64": "dGVzdA=="},
    )
    assert res.status_code == 403
