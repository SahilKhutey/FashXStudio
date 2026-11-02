from __future__ import annotations

import io
from uuid import UUID, uuid4

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentImage
from fashx.application.ports.tryon import TryOnError, TryOnOutput, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.watermarker import SyntheticWatermarker
from schemas.common.enums import DataType
from schemas.identity.consent import ConsentUpdate


def make_valid_test_image(
    width: int = 512,
    height: int = 768,
    primary: tuple[int, int, int] = (140, 120, 100),
    accent: tuple[int, int, int] = (200, 180, 160),
) -> bytes:
    img = Image.new("RGB", (width, height), primary)
    for x in range(width // 2):
        for y in range(height):
            img.putpixel((x, y), accent)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


async def setup_vto_job_fixture(
    session_factory: async_sessionmaker[AsyncSession],
    storage: InMemoryStorageAdapter,
) -> tuple[UUID, UUID, UUID, UUID]:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)

    # 1. User with body_photo consent
    create_uc = CreateProfileUseCase(profile_uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )
    user_id = profile.user_id

    # 2. Accepted portrait photo
    photo_bytes = make_valid_test_image(512, 768)
    photo_key = f"u/{user_id}/photos/portrait.jpg"
    await storage.put(photo_key, photo_bytes)

    async with profile_uow:
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key=photo_key,
            status="accepted",
            ready_for_tryon=True,
            content_sha256="sha-photo-001",
        )
        photo_id = photo.id
        await profile_uow.commit()

    # 3. Canonical garment and primary image
    garment_id = uuid4()
    garment_bytes = make_valid_test_image(512, 512, primary=(30, 60, 120), accent=(90, 140, 210))
    garment_key = f"catalog/garments/{garment_id}.jpg"
    await storage.put(garment_key, garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Shirt",
            category="tops",
            gender="unisex",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        garment_img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_key,
            content_hash="sha-garment-001",
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(garment_img)
        await catalog_uow.commit()

    # 4. Queued TryOnJob
    job_id = uuid4()
    async with tryon_uow:
        await tryon_uow.jobs.create(
            id_=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"tryon/artifact/{job_id}",
            model_version="tryon-v1.6",
            pipeline_version="fashn-hosted-v1",
        )
        await tryon_uow.commit()

    return user_id, garment_id, photo_id, job_id


@pytest.mark.asyncio
async def test_provider_submit_persists_provider_job_id_before_collection(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    db_job_id_at_collection_time: str | None = None

    class VerifyingAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"
        timeout_s = 60.0

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-remote-12345"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            nonlocal db_job_id_at_collection_time
            # Verify synchronously during collect that DB already has provider_job_id persisted
            import asyncio

            from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

            async def _check() -> None:
                nonlocal db_job_id_at_collection_time
                async with TryOnUnitOfWork(session_factory) as uow:
                    j = await uow.jobs.get_by_id(job_id)
                    if j:
                        db_job_id_at_collection_time = j.provider_job_id

            asyncio.run(_check())
            return TryOnOutput(
                image_bytes=make_valid_test_image(512, 768),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=150,
                cost_usd_est=0.075,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=VerifyingAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "completed"
    assert db_job_id_at_collection_time == "fashn-remote-12345"


@pytest.mark.asyncio
async def test_collection_timeout_requeues_preserving_provider_job_id(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class TimeoutAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"
        timeout_s = 60.0

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-remote-timeout-999"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            raise TryOnError(
                code="provider_timeout",
                user_message="Try-on took too long. We'll retry.",
                retryable=True,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=TimeoutAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "queued"
    assert res.failure_reason == "provider_timeout"

    # Reload from DB and verify provider_job_id preserved
    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "queued"
        assert reloaded.provider_job_id == "fashn-remote-timeout-999"


@pytest.mark.asyncio
async def test_provider_permanent_failure_marks_job_failed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class PermanentFailureAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-remote-fail-555"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            raise TryOnError(
                code="provider_failed",
                user_message="We couldn't generate this try-on.",
                retryable=False,
                detail="garment_pose_mismatch",
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=PermanentFailureAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "provider_failed"

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "failed"
        assert reloaded.failure_reason == "provider_failed"
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_provider_invalid_image_does_not_publish_artifact(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class InvalidImageAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-bad-img-job"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            # Solid black frame triggers quality rejection
            img = Image.new("RGB", (512, 512), (0, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            return TryOnOutput(
                image_bytes=buf.getvalue(),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=100,
                cost_usd_est=0.075,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=InvalidImageAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "quality_rejected"

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "failed"
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_watermark_failure_fails_job_and_publishes_no_artifact(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = InMemoryStorageAdapter()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class ValidAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-valid-job"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            return TryOnOutput(
                image_bytes=make_valid_test_image(512, 768),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=100,
                cost_usd_est=0.075,
            )

    def crashing_watermark(*args, **kwargs) -> bytes:
        raise RuntimeError("C2PA watermarking engine crashed")

    monkeypatch.setattr(SyntheticWatermarker, "apply_watermark", crashing_watermark)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=ValidAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "watermark_failed"

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "failed"
        assert reloaded.failure_reason == "watermark_failed"
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_consent_revoked_during_inference_discards_output(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class ConsentRevokingAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-consent-revoke-job"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            # Revoke consent mid-inference
            import asyncio

            from fashx.profile.repositories.profile_repository import ProfileUnitOfWork

            async def _revoke() -> None:
                async with ProfileUnitOfWork(session_factory) as puow:
                    record = await puow.consents.get_by_user_and_type(user_id, "body_photo")
                    if record:
                        record.granted = False
                    await puow.commit()

            asyncio.run(_revoke())
            return TryOnOutput(
                image_bytes=make_valid_test_image(512, 768),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=100,
                cost_usd_est=0.075,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=ConsentRevokingAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "cancelled"
    assert res.failure_reason == "consent_revoked"

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "cancelled"
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_storage_write_failure_fails_job_without_completion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    class FailingStorage(InMemoryStorageAdapter):
        async def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
            if "tryon_result" in key or "tryon" in key:
                raise OSError("S3 upload failed: bucket unreachable")
            return await super().put(key, data, content_type)

    storage = FailingStorage()
    _, _, _, job_id = await setup_vto_job_fixture(session_factory, storage)

    class ValidAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-valid-storage-test"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            return TryOnOutput(
                image_bytes=make_valid_test_image(512, 768),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=100,
                cost_usd_est=0.075,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=ValidAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "storage_error"

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "failed"
        assert reloaded.failure_reason == "storage_error"
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_provider_valid_image_runs_quality_gate_and_persists_artifact(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_job_fixture(session_factory, storage)

    class ValidAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "fashn-hosted-v1"

        def submit(self, req: TryOnRequest) -> str:
            return "fashn-valid-success-job"

        def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
            return TryOnOutput(
                image_bytes=make_valid_test_image(512, 768),
                provider=self.provider,
                model=self.model_version,
                provider_job_id=provider_job_id,
                latency_ms=120,
                cost_usd_est=0.075,
            )

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=ValidAdapter(),
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "completed"
    assert res.failure_reason is None

    async with TryOnUnitOfWork(session_factory) as uow:
        reloaded = await uow.jobs.get_by_id(job_id)
        assert reloaded is not None
        assert reloaded.status == "completed"
        assert reloaded.completed_at is not None

        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is not None
        assert artifact.result_key is not None
        assert await storage.exists(artifact.result_key)
        assert artifact.photo_version == 1
        assert artifact.garment_version == 1
