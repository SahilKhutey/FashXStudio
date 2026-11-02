from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentImage
from database.models.tryon import TryOnArtifact
from fashx.application.ports.tryon import TryOnError, TryOnOutput, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ConsentRequiredError, ValidationError
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.errors import ApiError
from fashx.tryon.adapters.mock_adapter import MockTryOnAdapter
from fashx.tryon.application.create_job import (
    CreateTryOnCommand,
    CreateTryOnJobUseCase,
)
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.application.worker import TryOnWorker
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from schemas.common.enums import DataType
from schemas.identity.consent import ConsentUpdate


def make_test_image(
    width: int = 512,
    height: int = 768,
    primary_color: tuple[int, int, int] = (140, 120, 100),
    accent_color: tuple[int, int, int] = (200, 180, 160),
) -> bytes:
    import io

    from PIL import Image

    img = Image.new("RGB", (width, height), primary_color)
    for x in range(width // 2):
        for y in range(height):
            img.putpixel((x, y), accent_color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_create_job_is_idempotent(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()
    idempotency_key = "idemp-key-001"

    async with uow:
        job1 = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key=idempotency_key,
            artifact_key="tryon/test/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        await uow.commit()

    async with uow:
        job2 = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key=idempotency_key,
            artifact_key="tryon/test/002",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        assert job2.id == job1.id
        assert job2.artifact_key == "tryon/test/001"


@pytest.mark.asyncio
async def test_claim_next_job_sets_worker_lease(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with uow:
        job = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="claim-test-key",
            artifact_key="tryon/claim/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        await uow.commit()

    # Worker 1 claims job
    async with uow:
        claimed = await uow.jobs.claim_next_job("worker-alpha", lease_seconds=120)
        assert claimed is not None
        assert claimed.id == job.id
        assert claimed.status == "running"
        assert claimed.locked_by == "worker-alpha"
        assert claimed.locked_at is not None
        assert claimed.attempt_count == 1
        await uow.commit()

    # Worker 2 tries to claim: active lease prevents second claim
    async with uow:
        second_claimed = await uow.jobs.claim_next_job("worker-beta", lease_seconds=120)
        assert second_claimed is None


@pytest.mark.asyncio
async def test_renew_and_release_lease(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with uow:
        job = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="lease-test-key",
            artifact_key="tryon/lease/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        await uow.commit()

    async with uow:
        claimed = await uow.jobs.claim_next_job("worker-alpha", lease_seconds=120)
        assert claimed is not None
        initial_locked_at = claimed.locked_at
        await uow.commit()

    # Renew lease with correct worker
    async with uow:
        renewed = await uow.jobs.renew_lease(job.id, "worker-alpha", lease_seconds=120)
        assert renewed is True
        # Wrong worker fails to renew
        renewed_wrong = await uow.jobs.renew_lease(job.id, "worker-intruder", lease_seconds=120)
        assert renewed_wrong is False
        await uow.commit()

    # Release lease
    async with uow:
        released = await uow.jobs.release_lease(job.id, "worker-alpha")
        assert released is True
        db_job = await uow.jobs.get_by_id(job.id)
        assert db_job is not None
        assert db_job.locked_at is None
        assert db_job.locked_by is None


@pytest.mark.asyncio
async def test_stale_job_recovery(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with uow:
        job = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="stale-test-key",
            artifact_key="tryon/stale/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        # Mark as running with expired lease
        job.status = "running"
        job.locked_at = datetime.now(UTC) - timedelta(seconds=300)
        job.locked_by = "worker-crashed"
        await uow.commit()

    # Recovery worker claims expired job
    async with uow:
        recovered = await uow.jobs.claim_next_job("worker-recovery", lease_seconds=120)
        assert recovered is not None
        assert recovered.id == job.id
        assert recovered.locked_by == "worker-recovery"
        assert recovered.attempt_count == 1
        await uow.commit()


@pytest.mark.asyncio
async def test_request_cancel_queued_and_running(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()

    async with uow:
        job = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="cancel-test-key",
            artifact_key="tryon/cancel/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        await uow.commit()

    # Queued job cancel sets status=cancelled immediately
    async with uow:
        cancelled = await uow.jobs.request_cancel(job.id, user_id)
        assert cancelled is not None
        assert cancelled.status == "cancelled"
        assert cancelled.cancel_requested is True
        assert cancelled.failure_reason == "cancelled_by_user"
        await uow.commit()

    # Running job cancel marks cancel_requested=True
    async with uow:
        job2 = await uow.jobs.create(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="cancel-running-key",
            artifact_key="tryon/cancel/002",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        job2.status = "running"
        job2.locked_by = "worker-1"
        await uow.commit()

    async with uow:
        cancel_running = await uow.jobs.request_cancel(job2.id, user_id)
        assert cancel_running is not None
        assert cancel_running.cancel_requested is True
        assert cancel_running.status == "running"  # worker cooperatively cancels


@pytest.mark.asyncio
async def test_create_tryon_job_use_case_lifecycle(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    # 1. Setup User with body_photo consent
    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )

    # 2. Setup accepted photo
    photo_id = uuid4()
    async with profile_uow:
        photo = await profile_uow.photos.create(
            id_=photo_id,
            user_id=profile.user_id,
            photo_type="tryon_reference",
            storage_key="u/test/photo.jpg",
            status="accepted",
            ready_for_tryon=True,
            content_sha256="abc123hash",
        )
        await profile_uow.commit()

    # 3. Setup canonical garment
    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Classic Jacket",
            category="tops",
            gender="unisex",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    use_case = CreateTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),  # type: ignore[arg-type]
    )

    # 4. Create Job
    cmd = CreateTryOnCommand(
        user_id=profile.user_id,
        garment_id=garment_id,
        photo_id=photo_id,
        idempotency_key="uc-idemp-001",
    )
    result = await use_case.execute(cmd)
    assert result.status == "queued"
    assert result.reused is False
    assert result.job_id is not None

    # 5. Idempotent re-submission returns same job with reused=True
    second_result = await use_case.execute(cmd)
    assert second_result.job_id == result.job_id
    assert second_result.reused is True


@pytest.mark.asyncio
async def test_create_tryon_job_use_case_requires_consent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    # User created WITHOUT body_photo consent
    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(CreateProfileCommand())

    use_case = CreateTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),  # type: ignore[arg-type]
    )

    cmd = CreateTryOnCommand(
        user_id=profile.user_id,
        garment_id=uuid4(),
        idempotency_key="no-consent-key",
    )
    with pytest.raises(ConsentRequiredError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_create_tryon_job_use_case_rejects_unowned_photo(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )

    use_case = CreateTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),  # type: ignore[arg-type]
    )

    # Passing someone else's or non-existent photo_id
    cmd = CreateTryOnCommand(
        user_id=profile.user_id,
        garment_id=uuid4(),
        photo_id=uuid4(),
        idempotency_key="unowned-photo-key",
    )
    with pytest.raises(ValidationError) as exc:
        await use_case.execute(cmd)
    assert exc.value.field == "photo_id"


@pytest.mark.asyncio
async def test_worker_polling_and_execution_lifecycle(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # 1. Setup User and accepted photo
    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )
    photo_bytes = make_test_image(512, 768, primary_color=(150, 120, 110), accent_color=(210, 180, 170))
    await storage.put("u/worker/photo.jpg", photo_bytes)

    async with profile_uow:
        photo = await profile_uow.photos.create(
            user_id=profile.user_id,
            photo_type="tryon_reference",
            storage_key="u/worker/photo.jpg",
            status="accepted",
            ready_for_tryon=True,
        )
        await profile_uow.commit()

    # 2. Setup garment and garment image
    garment_id = uuid4()
    garment_bytes = make_test_image(512, 512, primary_color=(40, 70, 130), accent_color=(90, 130, 200))
    await storage.put("garments/test/jacket.jpg", garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Worker Jacket",
            category="tops",
            gender="unisex",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        garment_img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key="garments/test/jacket.jpg",
            content_hash="hash-worker-garment-001",
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(garment_img)
        await catalog_uow.commit()

    # 3. Create Queued Job
    use_case = CreateTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),
    )
    cmd = CreateTryOnCommand(
        user_id=profile.user_id,
        garment_id=garment_id,
        photo_id=photo.id,
        idempotency_key="worker-test-job-001",
    )
    create_res = await use_case.execute(cmd)
    assert create_res.status == "queued"

    # 4. Worker claims and processes job
    def make_process_uc() -> ProcessTryOnJobUseCase:
        return ProcessTryOnJobUseCase(
            tryon_uow=TryOnUnitOfWork(session_factory),
            profile_uow=ProfileUnitOfWork(session_factory),
            catalog_uow=CatalogUnitOfWork(session_factory),
            adapter=MockTryOnAdapter(),
            storage=storage,
        )

    worker = TryOnWorker(
        uow_factory=lambda: TryOnUnitOfWork(session_factory),
        process_job_factory=make_process_uc,
        worker_id="worker-ci-001",
        poll_seconds=0.1,
    )

    # Process one job end-to-end via worker.process_one()
    processed_res = await worker.process_one()
    assert processed_res is not None
    assert processed_res.job_id == create_res.job_id
    assert processed_res.status == "completed"

    # Verify final completed job in DB
    async with tryon_uow:
        db_job = await tryon_uow.jobs.get_by_id(processed_res.job_id)
        assert db_job is not None
        assert db_job.status == "completed"
        assert db_job.locked_at is None
        assert db_job.locked_by is None
        assert db_job.completed_at is not None

        artifact = await tryon_uow.artifacts.get_by_job_id(processed_res.job_id)
        assert artifact is not None
        assert artifact.photo_version == 1
        assert artifact.garment_version == 1


@pytest.mark.asyncio
async def test_create_tryon_job_rejects_unsupported_garment_category(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )

    async with profile_uow:
        await profile_uow.photos.create(
            user_id=profile.user_id,
            photo_type="tryon_reference",
            storage_key="u/unsupported/photo.jpg",
            status="accepted",
            ready_for_tryon=True,
        )
        await profile_uow.commit()

    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Hiking Boots",
            category="shoes",
            gender="unisex",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    use_case = CreateTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),
    )
    cmd = CreateTryOnCommand(
        user_id=profile.user_id,
        garment_id=garment_id,
        idempotency_key="unsupported-cat-key",
    )
    with pytest.raises(ApiError) as exc:
        await use_case.execute(cmd)
    assert exc.value.status == 422
    assert exc.value.code == "unsupported_garment"


@pytest.mark.asyncio
async def test_worker_preserves_provider_job_id_on_collection_retry(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )
    photo_bytes = make_test_image(512, 768)
    garment_bytes = make_test_image(512, 512, (50, 80, 150), (100, 150, 220))

    async with profile_uow:
        photo = await profile_uow.photos.create(
            user_id=profile.user_id,
            photo_type="tryon_reference",
            storage_key="u/retry/photo.jpg",
            status="accepted",
            ready_for_tryon=True,
        )
        await profile_uow.commit()

    garment_id = uuid4()
    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Retry Garment",
            category="tops",
            gender="unisex",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    async with tryon_uow:
        job = await tryon_uow.jobs.create(
            user_id=profile.user_id,
            garment_id=garment_id,
            profile_photo_id=photo.id,
            idempotency_key="retry-test-001",
            artifact_key="tryon/retry/001",
            model_version="test-model",
            pipeline_version="test-pipe",
        )
        await tryon_uow.commit()

    class TimeoutAdapter:
        provider = "fashn"
        model_version = "fashn-v1"
        pipeline_version = "fashn-pipe-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-remote-job-999"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            raise TryOnError(
                code="provider_timeout",
                user_message="Provider timed out during rendering",
                retryable=True,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=TimeoutAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(
        job.id,
        user_photo_bytes=photo_bytes,
        garment_image_bytes=garment_bytes,
    )
    assert res.status == "queued"
    assert res.failure_reason == "provider_timeout"

    # Verify provider_job_id was preserved and attempt count increased
    async with tryon_uow:
        reloaded = await tryon_uow.jobs.get_by_id(job.id)
        assert reloaded is not None
        assert reloaded.status == "queued"
        assert reloaded.provider_job_id == "fashn-remote-job-999"
        assert reloaded.attempts == 2


def test_tryon_api_endpoints_cancel_and_result(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    from fastapi.testclient import TestClient

    from fashx.core.dependencies import get_storage
    from fashx.main import create_app
    from fashx.security.deps import get_identity_repo
    from fashx.security.identity import InMemoryIdentityRepo
    from fashx.tryon.router import get_tryon_uow
    from tests.conftest import make_token

    storage = InMemoryStorageAdapter()
    identity_repo = InMemoryIdentityRepo()
    user_a = asyncio.run(identity_repo.resolve("fashx-test", "user-a"))
    user_b = asyncio.run(identity_repo.resolve("fashx-test", "user-b"))
    user_a_uuid = UUID(user_a.user_id)

    app = create_app()
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    app.dependency_overrides[get_storage] = lambda: storage

    token_a = make_token(sub="user-a")
    token_b = make_token(sub="user-b")
    client_a = TestClient(app, headers={"Authorization": f"Bearer {token_a}"})
    client_b = TestClient(app, headers={"Authorization": f"Bearer {token_b}"})

    uow = TryOnUnitOfWork(session_factory)

    job_id = uuid4()
    photo_id = uuid4()
    garment_id = uuid4()

    async def _setup() -> None:
        async with uow:
            await uow.jobs.create(
                id_=job_id,
                user_id=user_a_uuid,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="api-endpoint-test-001",
                artifact_key="tryon/api-test/001",
                model_version="test-model",
                pipeline_version="test-pipe",
            )
            await uow.commit()

    asyncio.run(_setup())

    # 1. User B cannot cancel User A's job (returns 404 / not found)
    res_b_cancel = client_b.post(f"/api/v1/tryon/jobs/{job_id}/cancel")
    assert res_b_cancel.status_code == 404

    # 2. User A cannot get result while job is queued (returns 409 conflict)
    res_result_queued = client_a.get(f"/api/v1/tryon/jobs/{job_id}/result")
    assert res_result_queued.status_code == 409

    # 3. User A successfully cancels the queued job
    res_a_cancel = client_a.post(f"/api/v1/tryon/jobs/{job_id}/cancel")
    assert res_a_cancel.status_code == 200
    data = res_a_cancel.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "cancelled"

    # 4. Create completed job with artifact
    completed_job_id = uuid4()
    artifact_key = "tryon/api-test/completed-001"

    async def _setup_completed() -> None:
        async with uow:
            cjob = await uow.jobs.create(
                id_=completed_job_id,
                user_id=user_a_uuid,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="api-completed-test-001",
                artifact_key=artifact_key,
                model_version="test-model",
                pipeline_version="test-pipe",
            )
            cjob.status = "completed"
            cjob.completed_at = datetime.now(UTC)
            artifact = TryOnArtifact(
                job_id=completed_job_id,
                artifact_key=artifact_key,
                result_key="u/user-a/tryon/completed.jpg",
                model_version="test-model",
                pipeline_version="test-pipe",
                photo_version=1,
                garment_version=1,
            )
            uow.artifacts.add(artifact)
            await uow.commit()

    asyncio.run(_setup_completed())

    # 5. User A gets signed result URL
    res_result_completed = client_a.get(f"/api/v1/tryon/jobs/{completed_job_id}/result")
    assert res_result_completed.status_code == 200
    res_data = res_result_completed.json()
    assert res_data["job_id"] == str(completed_job_id)
    assert "result_url" in res_data
    assert "completed.jpg" in res_data["result_url"]

    # 6. User B cannot get User A's result (404)
    res_b_result = client_b.get(f"/api/v1/tryon/jobs/{completed_job_id}/result")
    assert res_b_result.status_code == 404
