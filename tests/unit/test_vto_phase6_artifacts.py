from __future__ import annotations

import hashlib
import io
from typing import Any
from uuid import UUID, uuid4

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentImage
from fashx.application.ports.tryon import TryOnOutput, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.artifact_metadata import ArtifactMetadata, inspect_artifact
from fashx.tryon.quality_validator import PostInferenceQualityValidator
from fashx.tryon.repositories.tryon_repository import TryOnArtifactRepository, TryOnUnitOfWork
from fashx.tryon.watermarker import SyntheticWatermarker
from schemas.common.enums import DataType
from schemas.identity.consent import ConsentUpdate


def make_image(
    image_format: str = "PNG",
    size: tuple[int, int] = (512, 512),
    color: tuple[int, int, int] = (100, 140, 180),
) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    return buffer.getvalue()


def make_contrasty_image(
    image_format: str = "PNG",
    size: tuple[int, int] = (512, 512),
) -> bytes:
    image = Image.new("RGB", size)
    pixels = image.load()
    w, h = size
    for y in range(h):
        for x in range(w):
            value = 40 if (x // 16 + y // 16) % 2 else 210
            pixels[x, y] = (value, value, value)
    buffer = io.BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


async def setup_vto_fixture(
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
    photo_bytes = make_contrasty_image("JPEG", (512, 768))
    photo_key = f"u/{user_id}/photos/portrait.jpg"
    await storage.put(photo_key, photo_bytes)

    async with profile_uow:
        photo = await profile_uow.photos.create(
            user_id=user_id,
            photo_type="tryon_reference",
            storage_key=photo_key,
            status="accepted",
            ready_for_tryon=True,
            content_sha256="sha-photo-p6",
        )
        photo_id = photo.id
        await profile_uow.commit()

    # 3. Canonical garment and primary image
    garment_id = uuid4()
    garment_bytes = make_contrasty_image("JPEG", (512, 512))
    garment_key = f"catalog/garments/{garment_id}.jpg"
    await storage.put(garment_key, garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Silk Blouse",
            category="tops",
            gender="women",
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        garment_img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_key,
            content_hash="sha-garment-p6",
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


# ---------------------------------------------------------------------------
# 1. PostInferenceQualityValidator Unit Tests
# ---------------------------------------------------------------------------


def test_validator_rejects_empty_payload() -> None:
    res = PostInferenceQualityValidator.validate(b"")
    assert res.is_acceptable is False
    assert res.failure_reason == "Empty image payload"


def test_validator_rejects_corrupted_bytes() -> None:
    res = PostInferenceQualityValidator.validate(b"NOT_AN_IMAGE_PAYLOAD_123456")
    assert res.is_acceptable is False
    assert "Image decoding error" in (res.failure_reason or "")


def test_validator_rejects_unsupported_format() -> None:
    # GIF format is not in ALLOWED_FORMATS
    buf = io.BytesIO()
    Image.new("RGB", (512, 512), (120, 130, 140)).save(buf, format="GIF")
    res = PostInferenceQualityValidator.validate(buf.getvalue())
    assert res.is_acceptable is False
    assert "Unsupported image format: GIF" in (res.failure_reason or "")


def test_validator_rejects_below_minimum_dimension() -> None:
    # 200x200 is below MIN_DIMENSION (256)
    img = make_contrasty_image("PNG", (200, 200))
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is False
    assert "resolution below minimum threshold" in (res.failure_reason or "")


def test_validator_rejects_exceeding_max_side() -> None:
    # 4097x256 exceeds MAX_SIDE (4096)
    img = make_image("PNG", (4097, 256))
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is False
    assert "dimension exceeds maximum allowed side" in (res.failure_reason or "")


def test_validator_rejects_payload_exceeding_max_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Set MAX_BYTES lower to test limit without allocating huge memory
    monkeypatch.setattr(PostInferenceQualityValidator, "MAX_BYTES", 1000)
    img = make_contrasty_image("PNG", (512, 512))
    assert len(img) > 1000
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is False
    assert "payload exceeds maximum allowed size" in (res.failure_reason or "")


def test_validator_rejects_underexposed_black_frame() -> None:
    black = make_image("PNG", (512, 512), (5, 5, 5))
    res = PostInferenceQualityValidator.validate(black)
    assert res.is_acceptable is False
    assert "underexposed / black frame" in (res.failure_reason or "")


def test_validator_rejects_overexposed_white_frame() -> None:
    white = make_image("PNG", (512, 512), (250, 250, 250))
    res = PostInferenceQualityValidator.validate(white)
    assert res.is_acceptable is False
    assert "blown out / overexposed white frame" in (res.failure_reason or "")


def test_validator_rejects_low_contrast_flat_frame() -> None:
    flat = make_image("PNG", (512, 512), (128, 128, 128))
    res = PostInferenceQualityValidator.validate(flat)
    assert res.is_acceptable is False
    assert "lacks contrast / solid flat artifact" in (res.failure_reason or "")


def test_validator_accepts_healthy_contrasty_png() -> None:
    img = make_contrasty_image("PNG", (512, 512))
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is True
    assert res.failure_reason is None
    assert res.structural_score > 0.5
    assert res.contrast_score >= 12.0
    assert 25.0 <= res.mean_luminance <= 235.0


def test_validator_accepts_healthy_contrasty_jpeg() -> None:
    img = make_contrasty_image("JPEG", (512, 512))
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is True
    assert res.failure_reason is None


def test_validator_accepts_healthy_contrasty_webp() -> None:
    img = make_contrasty_image("WEBP", (512, 512))
    res = PostInferenceQualityValidator.validate(img)
    assert res.is_acceptable is True
    assert res.failure_reason is None


# ---------------------------------------------------------------------------
# 2. inspect_artifact Unit Tests
# ---------------------------------------------------------------------------


def test_inspect_artifact_empty_raises() -> None:
    with pytest.raises(ValueError, match="Artifact cannot be empty"):
        inspect_artifact(b"")


def test_inspect_artifact_corrupt_raises() -> None:
    with pytest.raises(Exception):
        inspect_artifact(b"not_an_image")


def test_inspect_artifact_unsupported_format_raises() -> None:
    buf = io.BytesIO()
    Image.new("RGB", (300, 300)).save(buf, format="GIF")
    with pytest.raises(ValueError, match="Unsupported artifact format"):
        inspect_artifact(buf.getvalue())


def test_inspect_artifact_png() -> None:
    data = make_image("PNG", (400, 600))
    meta = inspect_artifact(data)
    assert isinstance(meta, ArtifactMetadata)
    assert meta.content_type == "image/png"
    assert meta.extension == ".png"
    assert meta.width == 400
    assert meta.height == 600
    assert meta.size_bytes == len(data)
    assert meta.content_sha256 == hashlib.sha256(data).hexdigest()


def test_inspect_artifact_jpeg() -> None:
    data = make_image("JPEG", (300, 500))
    meta = inspect_artifact(data)
    assert meta.content_type == "image/jpeg"
    assert meta.extension == ".jpg"
    assert meta.width == 300
    assert meta.height == 500
    assert meta.content_sha256 == hashlib.sha256(data).hexdigest()


def test_inspect_artifact_webp() -> None:
    data = make_image("WEBP", (350, 450))
    meta = inspect_artifact(data)
    assert meta.content_type == "image/webp"
    assert meta.extension == ".webp"
    assert meta.width == 350
    assert meta.height == 450
    assert meta.content_sha256 == hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 3. ProcessTryOnJobUseCase Process-Level Integration Tests (Phase 6)
# ---------------------------------------------------------------------------


class MockInferenceAdapter:
    def __init__(self, output_bytes: bytes, model_version: str = "tryon-v1.6") -> None:
        self.output_bytes = output_bytes
        self.model_version = model_version
        self.pipeline_version = "fashn-hosted-v1"
        self.timeout_s = 60.0

    def submit(self, req: TryOnRequest) -> str:
        return "mock_job_p6"

    def collect(self, provider_job_id: str, *, deadline_s: float = 60.0) -> TryOnOutput:
        return TryOnOutput(
            image_bytes=self.output_bytes,
            provider="mock_p6",
            model=self.model_version,
            provider_job_id=provider_job_id,
            latency_ms=120,
            cost_usd_est=0.075,
        )


@pytest.mark.asyncio
async def test_phase6_valid_artifact_persists_full_metadata_and_png_consistency(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 768))
    adapter = MockInferenceAdapter(render_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "completed"
    assert res.failure_reason is None
    assert res.result_url is not None

    async with TryOnUnitOfWork(session_factory) as uow:
        job = await uow.jobs.get_by_id(job_id)
        assert job is not None
        assert job.status == "completed"

        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is not None
        assert artifact.quality_status == "accepted"
        # Watermarker returns PNG, so MIME type and extension must agree on PNG
        assert artifact.content_type == "image/png"
        assert artifact.result_key.endswith(".png")
        assert artifact.result_key.startswith(f"u/{user_id}/tryon/")
        assert artifact.width == 512
        assert artifact.height == 768
        assert artifact.size_bytes is not None and artifact.size_bytes > 0
        assert artifact.content_sha256 is not None and len(artifact.content_sha256) == 64
        assert artifact.quality_score is not None and artifact.quality_score > 0.5

        # Check stored bytes match SHA-256
        stored_bytes = await storage.get(artifact.result_key)
        assert stored_bytes is not None
        assert hashlib.sha256(stored_bytes).hexdigest() == artifact.content_sha256


@pytest.mark.asyncio
async def test_phase6_corrupt_provider_image_fails_without_artifact(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    # Provider returns undecodable bytes
    adapter = MockInferenceAdapter(b"CORRUPT_BYTES_XYZ")

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "quality_rejected"

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_low_quality_output_fails_with_quality_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    # Completely flat gray image fails contrast check
    flat_bytes = make_image("PNG", (512, 512), (128, 128, 128))
    adapter = MockInferenceAdapter(flat_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "quality_rejected"

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_watermark_failure_fails_with_watermark_failed(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))
    adapter = MockInferenceAdapter(render_bytes)

    def _boom(*args: Any, **kwargs: Any) -> bytes:
        raise RuntimeError("Watermark engine font missing")

    monkeypatch.setattr(SyntheticWatermarker, "apply_watermark", _boom)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "watermark_failed"

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_storage_unreachable_fails_without_artifact(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    class FailingStorage(InMemoryStorageAdapter):
        async def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
            if "tryon" in key:
                raise OSError("S3 connection timeout")
            return await super().put(key, data, content_type)

    storage = FailingStorage()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))
    adapter = MockInferenceAdapter(render_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "storage_error"

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_db_failure_after_storage_triggers_storage_cleanup(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))
    adapter = MockInferenceAdapter(render_bytes)

    def _failing_add(self: Any, artifact: Any) -> None:
        raise RuntimeError("Database constraint error during artifact insert")

    monkeypatch.setattr(TryOnArtifactRepository, "add", _failing_add)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "failed"
    assert res.failure_reason == "storage_error"

    # Verify storage cleanup was attempted (the expected tryon key was deleted)
    expected_key = f"u/{user_id}/tryon/{job_id}.png"
    assert not await storage.exists(expected_key)


@pytest.mark.asyncio
async def test_phase6_consent_revoked_after_storage_triggers_cleanup_and_cancellation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))

    class ConsentRevokingAdapter(MockInferenceAdapter):
        def collect(self, provider_job_id: str, *, deadline_s: float = 60.0) -> TryOnOutput:
            # Revoke user consent right after collection
            import asyncio

            from fashx.profile.repositories.profile_repository import ProfileUnitOfWork

            async def _revoke() -> None:
                async with ProfileUnitOfWork(session_factory) as uow:
                    rec = await uow.consents.get_by_user_and_type(user_id, "body_photo")
                    if rec:
                        rec.granted = False
                        await uow.commit()

            asyncio.run(_revoke())
            return super().collect(provider_job_id, deadline_s=deadline_s)

    adapter = ConsentRevokingAdapter(render_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "cancelled"
    assert res.failure_reason == "consent_revoked"

    expected_key = f"u/{user_id}/tryon/{job_id}.png"
    assert not await storage.exists(expected_key)

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_cancellation_requested_triggers_cleanup(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))

    class CancellingAdapter(MockInferenceAdapter):
        def collect(self, provider_job_id: str, *, deadline_s: float = 60.0) -> TryOnOutput:
            import asyncio

            from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

            async def _cancel() -> None:
                async with TryOnUnitOfWork(session_factory) as uow:
                    await uow.jobs.request_cancel(job_id, user_id)
                    await uow.commit()

            asyncio.run(_cancel())
            return super().collect(provider_job_id, deadline_s=deadline_s)

    adapter = CancellingAdapter(render_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "cancelled"
    assert res.failure_reason == "cancel_requested"

    expected_key = f"u/{user_id}/tryon/{job_id}.png"
    assert not await storage.exists(expected_key)

    async with TryOnUnitOfWork(session_factory) as uow:
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is None


@pytest.mark.asyncio
async def test_phase6_ownership_isolation_and_result_access(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    storage = InMemoryStorageAdapter()
    user_a_id, garment_id, photo_id, job_id = await setup_vto_fixture(session_factory, storage)

    render_bytes = make_contrasty_image("PNG", (512, 512))
    adapter = MockInferenceAdapter(render_bytes)

    proc_uc = ProcessTryOnJobUseCase(
        tryon_uow=TryOnUnitOfWork(session_factory),
        profile_uow=ProfileUnitOfWork(session_factory),
        catalog_uow=CatalogUnitOfWork(session_factory),
        adapter=adapter,
        storage=storage,
    )

    res = await proc_uc.execute(job_id)
    assert res.status == "completed"

    user_b_id = uuid4()
    async with TryOnUnitOfWork(session_factory) as uow:
        # User A owns the job
        owned_job_a = await uow.jobs.get_owned(job_id, user_a_id)
        assert owned_job_a is not None

        # User B does NOT own the job - isolation guaranteed
        owned_job_b = await uow.jobs.get_owned(job_id, user_b_id)
        assert owned_job_b is None

        # Artifact retrieval for job
        artifact = await uow.artifacts.get_by_job_id(job_id)
        assert artifact is not None
        assert artifact.result_key == f"u/{user_a_id}/tryon/{job_id}.png"

        # Signed URL generation for authorized user
        signed_url = storage.signed_get_url(artifact.result_key, ttl_s=3600)
        assert artifact.result_key in signed_url
        assert "exp=3600" in signed_url
