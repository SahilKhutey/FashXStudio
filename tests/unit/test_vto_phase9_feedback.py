from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.identity import User
from database.models.tryon import TryOnJob
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.submit_tryon_feedback import (
    SubmitTryOnFeedbackCommand,
    SubmitTryOnFeedbackUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.commerce_wardrobe.router import (
    get_catalog_uow,
    get_commerce_uow,
    get_profile_uow,
    get_tryon_uow,
)
from fashx.commerce_wardrobe.router import (
    router as commerce_router,
)
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.errors import AuthorizationError, NotFoundError, ValidationError
from fashx.gateway.errors import install_exception_handlers
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from tests.conftest import make_token


def _create_test_app(
    session_factory: async_sessionmaker[AsyncSession],
    storage: Any,
) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    install_exception_handlers(app)
    repo = InMemoryIdentityRepo()

    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_commerce_uow] = lambda: CommerceWardrobeUnitOfWork(session_factory)
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_storage] = lambda: storage

    app.include_router(commerce_router)
    return TestClient(app), repo


async def _seed_job(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: UUID,
    job_id: UUID,
    status: str = "completed",
    provider: str = "fashn",
) -> TryOnJob:
    profile_uow = ProfileUnitOfWork(session_factory)
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    tryon_uow = TryOnUnitOfWork(session_factory)
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=uuid4(),
            profile_photo_id=uuid4(),
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"artifacts/{job_id}.png",
            status=status,
            model_version="v1",
            pipeline_version="v1",
            provider=provider,
            photo_version=1,
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()
    return job


@pytest.mark.asyncio
async def test_submit_feedback_use_case_success(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    job_id = uuid4()
    await _seed_job(session_factory, user_id, job_id, status="completed", provider="fashn")

    res = await uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=user_id,
            tryon_job_id=job_id,
            visual_accuracy="accurate",
            purchase_confidence=4,
            issue_tags=["unnatural_fit", "color_inaccurate"],
        )
    )

    assert res.feedback_id is not None
    assert res.user_id == user_id
    assert res.tryon_job_id == job_id
    assert res.visual_accuracy == "accurate"
    assert res.purchase_confidence == 4
    assert res.issue_tags == ["color_inaccurate", "unnatural_fit"]

    # Verify persisted in database
    async with uow:
        persisted = await uow.tryon_feedback.get_by_job_id(job_id)
        assert persisted is not None
        assert persisted.user_id == user_id
        assert persisted.visual_accuracy == "accurate"
        assert persisted.purchase_confidence == 4
        assert persisted.provider == "fashn"
        assert persisted.issue_tags == ["color_inaccurate", "unnatural_fit"]


@pytest.mark.asyncio
async def test_submit_feedback_use_case_validation_errors(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    job_id = uuid4()
    await _seed_job(session_factory, user_id, job_id, status="completed")

    # Invalid visual accuracy
    with pytest.raises(ValidationError, match="Invalid visual accuracy"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="super_real",
            )
        )

    # Invalid purchase confidence
    with pytest.raises(ValidationError, match="Purchase confidence must be between 1 and 5"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="neutral",
                purchase_confidence=0,
            )
        )

    with pytest.raises(ValidationError, match="Purchase confidence must be between 1 and 5"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="neutral",
                purchase_confidence=6,
            )
        )

    # Invalid issue tag
    with pytest.raises(ValidationError, match="Invalid issue tag"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="inaccurate",
                issue_tags=["unnatural_fit", "unknown_bad_tag"],
            )
        )


@pytest.mark.asyncio
async def test_submit_feedback_use_case_job_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    non_existent_job_id = uuid4()

    with pytest.raises(NotFoundError, match="Try-on job .* not found"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=non_existent_job_id,
                visual_accuracy="accurate",
            )
        )


@pytest.mark.asyncio
async def test_submit_feedback_use_case_job_wrong_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    owner_id = uuid4()
    imposter_id = uuid4()
    job_id = uuid4()
    await _seed_job(session_factory, owner_id, job_id, status="completed")

    with pytest.raises(AuthorizationError, match="cannot submit feedback"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=imposter_id,
                tryon_job_id=job_id,
                visual_accuracy="accurate",
            )
        )


@pytest.mark.asyncio
async def test_submit_feedback_use_case_job_incomplete(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    job_id = uuid4()
    await _seed_job(session_factory, user_id, job_id, status="queued")

    with pytest.raises(ValidationError, match="Cannot submit feedback for job in status 'queued'"):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="accurate",
            )
        )


@pytest.mark.asyncio
async def test_submit_feedback_use_case_idempotent_duplicate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    job_id = uuid4()
    await _seed_job(session_factory, user_id, job_id, status="completed")

    res1 = await uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=user_id,
            tryon_job_id=job_id,
            visual_accuracy="accurate",
            purchase_confidence=5,
            issue_tags=["unnatural_fit"],
        )
    )

    # Repeat submission
    res2 = await uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=user_id,
            tryon_job_id=job_id,
            visual_accuracy="very_accurate",
            purchase_confidence=4,
            issue_tags=["color_inaccurate"],
        )
    )

    assert res2.feedback_id == res1.feedback_id
    assert res2.visual_accuracy == "accurate"
    assert res2.purchase_confidence == 5
    assert res2.issue_tags == ["unnatural_fit"]


@pytest.mark.asyncio
async def test_router_submit_tryon_feedback_omitting_user_id(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    user_id = UUID((await repo.resolve("fashx-test", "user-fb-1")).user_id)
    token = make_token(sub="user-fb-1")
    job_id = uuid4()
    await _seed_job(session_factory, user_id, job_id, status="completed", provider="fashn")

    resp = client.post(
        "/feedback/tryon",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tryon_job_id": str(job_id),
            "visual_accuracy": "very_accurate",
            "purchase_confidence": 5,
            "issue_tags": ["blurry_artifacts"],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user_id"] == str(user_id)
    assert data["tryon_job_id"] == str(job_id)
    assert data["visual_accuracy"] == "very_accurate"
    assert data["purchase_confidence"] == 5
    assert data["issue_tags"] == ["blurry_artifacts"]


@pytest.mark.asyncio
async def test_router_submit_tryon_feedback_mismatch_forbidden(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)
    client, repo = _create_test_app(session_factory, storage)

    await repo.resolve("fashx-test", "user-fb-auth")
    token = make_token(sub="user-fb-auth")
    job_id = uuid4()
    other_user_id = uuid4()

    resp = client.post(
        "/feedback/tryon",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": str(other_user_id),
            "tryon_job_id": str(job_id),
            "visual_accuracy": "accurate",
        },
    )
    assert resp.status_code == 403
