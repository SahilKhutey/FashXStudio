import io
from uuid import UUID, uuid4
import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, Merchant
from database.models.identity import User
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.application.ports.tryon import TryOnError, TryOnOutput, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ConsentRequiredError, EntityNotFoundError, ValidationError
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.errors import ApiError
from fashx.tryon.adapters.mock_adapter import MockTryOnAdapter
from fashx.tryon.application.get_job_status import GetTryOnJobStatusUseCase
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.application.submit_job import SubmitTryOnJobCommand, SubmitTryOnJobUseCase
from fashx.tryon.ports_dispatch import DispatchResult
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


def _make_valid_jpeg(size=(512, 768)) -> bytes:
    img = Image.new("RGB", size, (140, 120, 100))
    for x in range(size[0] // 2):
        for y in range(size[1]):
            img.putpixel((x, y), (200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_rc05_t01_no_consent_rejects_submission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    with pytest.raises(ConsentRequiredError):
        await submit_uc.execute(
            SubmitTryOnJobCommand(
                user_id=user_id,
                garment_id=uuid4(),
                idempotency_key="t01-key",
            )
        )


@pytest.mark.asyncio
async def test_rc05_t02_photo_of_another_user_rejects_submission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_a = uuid4()
    user_b = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_a))
        profile_uow.users.add(User(id=user_b))
        await profile_uow.consents.record_mobile_consent(user_a, "2026.1")
        photo_b = await profile_uow.photos.create(
            user_id=user_b,
            photo_type="tryon_reference",
            storage_key="photos/user_b.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        foreign_photo_id = photo_b.id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    with pytest.raises(ValidationError, match="not found or not owned"):
        await submit_uc.execute(
            SubmitTryOnJobCommand(
                user_id=user_a,
                garment_id=uuid4(),
                photo_id=foreign_photo_id,
                idempotency_key="t02-key",
            )
        )


@pytest.mark.asyncio
async def test_rc05_t03_photo_not_accepted_rejects_submission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        pending_photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="photos/pending.jpg",
            status="pending",
        )
        await profile_uow.commit()
        photo_id = pending_photo.id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    with pytest.raises(ValidationError, match="must be 'accepted'"):
        await submit_uc.execute(
            SubmitTryOnJobCommand(
                user_id=user_id,
                garment_id=uuid4(),
                photo_id=photo_id,
                idempotency_key="t03-key",
            )
        )


@pytest.mark.asyncio
async def test_rc05_t04_ineligible_garment_rejects_submission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="photos/acc.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id

    async with catalog_uow:
        garment = CanonicalGarment(
            display_name="Non-Tryon Scarf",
            category="accessories",
            tryon_supported=False,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    with pytest.raises(ApiError) as exc_info:
        await submit_uc.execute(
            SubmitTryOnJobCommand(
                user_id=user_id,
                garment_id=garment_id,
                photo_id=photo_id,
                idempotency_key="t04-key",
            )
        )
    assert exc_info.value.code == "unsupported_garment"


@pytest.mark.asyncio
async def test_rc05_t05_idempotent_submission_returns_same_job(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="photos/valid.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id

    async with catalog_uow:
        garment = CanonicalGarment(
            display_name="Linen Tee",
            category="tops",
            tryon_supported=True,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    res1 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            photo_id=photo_id,
            idempotency_key="t05-key",
        )
    )
    res2 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            photo_id=photo_id,
            idempotency_key="t05-key",
        )
    )
    assert res1.job_id == res2.job_id
    assert res1.artifact_key == res2.artifact_key


@pytest.mark.asyncio
async def test_rc05_t06_artifact_cache_hit_skips_inference(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="photos/cached_photo.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id

    async with catalog_uow:
        garment = CanonicalGarment(
            display_name="Classic Blazer",
            category="tops",
            tryon_supported=True,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    submit_uc = SubmitTryOnJobUseCase(tryon_uow, profile_uow, catalog_uow)
    res1 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            photo_id=photo_id,
            idempotency_key="t06-key-1",
        )
    )

    # Manually mark as completed and add artifact
    async with tryon_uow:
        art = TryOnArtifact(
            job_id=res1.job_id,
            artifact_key=res1.artifact_key,
            result_key="tryon/cached_result.png",
            model_version="mock-vto-v1",
            pipeline_version="pilot-pipe-v1",
            photo_version=1,
            garment_version=1,
            quality_status="accepted",
            width=512,
            height=768,
            size_bytes=2048,
            content_type="image/png",
            content_sha256="dummy_sha",
        )
        tryon_uow.artifacts.add(art)
        await tryon_uow.jobs.update_status(res1.job_id, "completed")
        await tryon_uow.commit()

    # Second submission with fresh idempotency key but same inputs
    res2 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            photo_id=photo_id,
            idempotency_key="t06-key-fresh",
        )
    )
    assert res2.is_cached is True
    assert res2.status == "completed"
    assert res2.result_url == "tryon/cached_result.png"


@pytest.mark.asyncio
async def test_rc05_t09_t10_resume_collection_with_persisted_provider_job(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    user_id = uuid4()
    test_jpeg = _make_valid_jpeg()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="u/photo.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id
    await storage.put("u/photo.jpg", test_jpeg, content_type="image/jpeg")

    async with catalog_uow:
        garment = CanonicalGarment(display_name="Silk Blouse", category="tops", tryon_supported=True)
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id
    await storage.put(f"garments/{garment_id}/primary.jpg", test_jpeg, content_type="image/jpeg")

    job_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="t09-key",
            artifact_key="tryon/art-09",
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="fashn-hosted-v1",
            provider="fashn_api",
            provider_job_id="existing-fashn-job-999",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    submit_called = False
    collect_called = False

    class TrackingAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"
        timeout_s = 60.0

        def submit(self, req: TryOnRequest) -> str:
            nonlocal submit_called
            submit_called = True
            return "new-job-id"

        def collect(self, provider_job_id: str, deadline_s: float = 90.0) -> TryOnOutput:
            nonlocal collect_called
            collect_called = True
            assert provider_job_id == "existing-fashn-job-999"
            return TryOnOutput(
                image_bytes=_make_valid_jpeg(),
                provider="fashn_api",
                model="tryon-v1.6",
                provider_job_id=provider_job_id,
                latency_ms=150,
                cost_usd_est=0.075,
            )

    process_uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=TrackingAdapter(),
        storage=storage,
    )
    result = await process_uc.execute(
        job_id,
        user_photo_bytes=test_jpeg,
        garment_image_bytes=test_jpeg,
    )
    assert submit_called is False
    assert collect_called is True
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_rc05_t14_t15_consent_revocation_cancels_job(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    user_id = uuid4()
    test_jpeg = _make_valid_jpeg()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="u/revoked.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id

    async with catalog_uow:
        garment = CanonicalGarment(display_name="Knit Sweater", category="tops", tryon_supported=True)
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    job_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="t14-key",
            artifact_key="tryon/art-14",
            status="queued",
            model_version="mock-vto-v1",
            pipeline_version="pilot-pipe-v1",
            provider="mock",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    process_uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=MockTryOnAdapter(),
        storage=storage,
    )
    res = await process_uc.execute(job_id, user_photo_bytes=test_jpeg, garment_image_bytes=test_jpeg)
    assert res.status == "cancelled"
    assert res.failure_reason == "consent_revoked"


@pytest.mark.asyncio
async def test_rc05_t13_owner_isolation_in_status_and_artifacts(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_a = uuid4()
    user_b = uuid4()
    job_id = uuid4()
    photo_id = uuid4()
    artifact_key = "tryon/isolated-art"

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_a,
            garment_id=uuid4(),
            profile_photo_id=photo_id,
            idempotency_key="t13-key",
            artifact_key=artifact_key,
            status="completed",
            model_version="mock-vto-v1",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        art = TryOnArtifact(
            job_id=job_id,
            artifact_key=artifact_key,
            result_key="tryon/res-13.png",
            model_version="mock-vto-v1",
            pipeline_version="pilot-pipe-v1",
            photo_version=1,
            garment_version=1,
            quality_status="accepted",
            width=512,
            height=768,
            size_bytes=1000,
            content_type="image/png",
            content_sha256="hash-13",
        )
        tryon_uow.artifacts.add(art)
        await tryon_uow.commit()

    status_uc = GetTryOnJobStatusUseCase(tryon_uow=tryon_uow, profile_uow=profile_uow)

    res_a = await status_uc.execute(job_id, user_id=str(user_a))
    assert res_a.job_id == job_id

    with pytest.raises(EntityNotFoundError):
        await status_uc.execute(job_id, user_id=str(user_b))


@pytest.mark.asyncio
async def test_rc05_dispatcher_observability(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    user_id = uuid4()
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.record_mobile_consent(user_id, "2026.1")
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key="u/disp.jpg",
            status="accepted",
        )
        await profile_uow.commit()
        photo_id = photo.id

    async with catalog_uow:
        garment = CanonicalGarment(display_name="Disp Top", category="tops", tryon_supported=True)
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()
        garment_id = garment.id

    class FailingDispatcher:
        async def dispatch(self, job_id: UUID) -> DispatchResult:
            return DispatchResult(accepted=False, reason="BrokerConnectionError")

    submit_uc = SubmitTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        dispatcher=FailingDispatcher(),
    )
    result = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            photo_id=photo_id,
            idempotency_key="disp-obs-key",
        )
    )
    assert result.status == "queued"
    assert result.dispatch_accepted is False
    assert result.dispatch_reason == "BrokerConnectionError"
