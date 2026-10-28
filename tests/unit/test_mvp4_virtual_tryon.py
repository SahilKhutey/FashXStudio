from __future__ import annotations

import hashlib
import io
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentImage
from database.models.identity import User
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.application.upload_photo import UploadPhotoCommand, UploadUserPhotoUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import get_identity_repo
from fashx.security.errors import ApiError, api_error_handler
from fashx.security.identity import InMemoryIdentityRepo
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.application.submit_job import SubmitTryOnJobCommand, SubmitTryOnJobUseCase
from fashx.tryon.ports_dispatch import DirectTryOnJobDispatcher
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.router import get_catalog_uow, get_profile_uow, get_tryon_uow
from fashx.tryon.router import router as tryon_router
from schemas.common.enums import DataType
from schemas.identity.consent import ConsentUpdate
from tests.conftest import make_token


def _create_valid_portrait_bytes() -> bytes:
    # 600x800 RGB portrait image with valid luminance and contrast
    width, height = 600, 800
    color = (150, 120, 100)
    img = Image.new("RGB", (width, height), color)
    for x in range(width // 2):
        for y in range(height):
            img.putpixel(
                (x, y), (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
            )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_test_client(
    session_factory: async_sessionmaker[AsyncSession],
    storage: Any | None = None,
) -> tuple[TestClient, InMemoryIdentityRepo]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: repo
    app.dependency_overrides[get_profile_uow] = lambda: ProfileUnitOfWork(session_factory)
    app.dependency_overrides[get_catalog_uow] = lambda: CatalogUnitOfWork(session_factory)
    app.dependency_overrides[get_tryon_uow] = lambda: TryOnUnitOfWork(session_factory)
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    if storage is not None:
        app.dependency_overrides[get_storage] = lambda: storage
    app.include_router(tryon_router)
    return TestClient(app), repo


@pytest.mark.asyncio
async def test_artifact_endpoint_requires_auth_and_ownership(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.1: GET /tryon/artifacts/{artifact_key} requires auth (401) and owner match (403)."""
    storage = LocalStorage(tmp_path)
    client, repo = create_test_client(session_factory, storage)

    # Provision user_a and user_b
    identity_a = await repo.resolve("fashx-test", "user-a-sub")
    user_a_id = UUID(identity_a.user_id)
    token_a = make_token(sub="user-a-sub")

    identity_b = await repo.resolve("fashx-test", "user-b-sub")
    user_b_id = UUID(identity_b.user_id)
    token_b = make_token(sub="user-b-sub")

    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_a_id))
        profile_uow.users.add(User(id=user_b_id))
        await profile_uow.commit()

    job_id = uuid4()
    photo_id = uuid4()
    art_key = f"art-{job_id}"
    res_key = f"u/{user_a_id}/tryon/{job_id}.jpg"
    storage.put(res_key, _create_valid_portrait_bytes())

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_a_id,
            garment_id=uuid4(),
            profile_photo_id=photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=art_key,
            status="completed",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        artifact = TryOnArtifact(
            job_id=job_id,
            artifact_key=art_key,
            result_key=res_key,
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
            photo_version=1,
            garment_version=1,
        )
        tryon_uow.artifacts.add(artifact)
        await tryon_uow.commit()

    # 1. Unauthenticated request -> 401
    resp_unauth = client.get(f"/tryon/artifacts/{art_key}", headers={"Authorization": ""})
    assert resp_unauth.status_code == 401

    # 2. Authenticated as non-owner (user_b) -> 403 Forbidden
    resp_forbidden = client.get(
        f"/tryon/artifacts/{art_key}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_forbidden.status_code == 403
    assert "forbidden" in resp_forbidden.text.lower()

    # 3. Authenticated as owner (user_a) -> 200 OK
    resp_owner = client.get(
        f"/tryon/artifacts/{art_key}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_owner.status_code == 200
    data = resp_owner.json()
    assert data["artifact_key"] == art_key
    assert data["result_key"] == res_key


@pytest.mark.asyncio
async def test_process_job_fails_closed_when_photo_bytes_missing(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.2: Worker fails closed with missing_photo_bytes instead of using synthetic fallbacks."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    job_id = uuid4()
    photo_id = uuid4()

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.consents.upsert(user_id=user_id, data_type="body_photo", granted=True)
        await profile_uow.commit()

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Shirt",
            category="tops",
            subcategory="shirts",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=450000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"art-{job_id}",
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    result = await worker.execute(job_id=job_id)

    assert result.status == "failed"
    assert result.failure_reason in ("missing_photo", "missing_photo_bytes")


@pytest.mark.asyncio
async def test_process_job_fails_closed_when_garment_bytes_missing(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.2: Worker fails closed with missing_garment_image_bytes when garment image is absent."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    job_id = uuid4()

    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=_create_valid_portrait_bytes(),
        )
    )
    assert photo_res.status == "accepted"

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Shirt",
            category="tops",
            subcategory="shirts",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=450000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_res.photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"art-{job_id}",
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    result = await worker.execute(job_id=job_id)

    assert result.status == "failed"
    assert result.failure_reason == "missing_garment_image_bytes"


@pytest.mark.asyncio
async def test_process_job_succeeds_with_real_storage_bytes(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.2 & 4.3: Real storage pipeline loads bytes, performs inference, watermarks and stores artifact."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    job_id = uuid4()

    # 1. Setup User and Portrait
    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    portrait_bytes = _create_valid_portrait_bytes()
    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=portrait_bytes,
        )
    )
    assert photo_res.status == "accepted"

    # 2. Setup Garment and Image in Storage
    garment_img_key = f"catalog/garments/{garment_id}_primary.jpg"
    garment_bytes = _create_valid_portrait_bytes()
    storage.put(garment_img_key, garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Red Polo",
            category="tops",
            subcategory="polo",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=350000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        garment_img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_img_key,
            content_hash=hashlib.sha256(garment_bytes).hexdigest(),
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(garment_img)
        await catalog_uow.commit()

    # 3. Create Job
    art_key = f"art-{job_id}"
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_res.photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=art_key,
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    # 4. Run Process Worker
    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    result = await worker.execute(job_id=job_id)

    assert result.status == "completed"
    assert result.result_url is not None
    assert storage.exists(result.result_url)

    # Verify artifact record saved
    async with tryon_uow:
        saved_art = await tryon_uow.artifacts.get_by_artifact_key(art_key)
        assert saved_art is not None
        assert saved_art.job_id == job_id


@pytest.mark.asyncio
async def test_midflight_consent_revocation_cancels_job(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.1: If body_photo consent is revoked before inference, job is immediately cancelled."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    job_id = uuid4()

    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=_create_valid_portrait_bytes(),
        )
    )
    assert photo_res.status == "accepted"

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Shirt",
            category="tops",
            subcategory="shirts",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=450000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_res.photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=f"art-{job_id}",
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    # User revokes consent before worker inference
    async with profile_uow:
        await profile_uow.consents.upsert(user_id=user_id, data_type="body_photo", granted=False)
        await profile_uow.commit()

    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    result = await worker.execute(job_id=job_id)

    assert result.status == "cancelled"
    assert result.failure_reason == "consent_revoked"

    # Confirm no artifact was created
    async with tryon_uow:
        db_job = await tryon_uow.jobs.get_by_id(job_id)
        assert db_job.status == "cancelled"
        art = await tryon_uow.artifacts.get_by_job_id(job_id)
        assert art is None


@pytest.mark.asyncio
async def test_submit_job_with_direct_dispatcher(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.3: DirectTryOnJobDispatcher triggers worker synchronously upon submission."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()

    # 1. Setup User and Portrait
    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    portrait_bytes = _create_valid_portrait_bytes()
    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=portrait_bytes,
        )
    )
    assert photo_res.status == "accepted"

    # 2. Setup Garment and Image
    garment_img_key = f"catalog/garments/{garment_id}_direct.jpg"
    garment_bytes = _create_valid_portrait_bytes()
    storage.put(garment_img_key, garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Black Tee",
            category="tops",
            subcategory="t-shirt",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=250000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_img_key,
            content_hash=hashlib.sha256(garment_bytes).hexdigest(),
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(img)
        await catalog_uow.commit()

    # 3. Use DirectTryOnJobDispatcher wired to ProcessTryOnJobUseCase
    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    dispatcher = DirectTryOnJobDispatcher(worker)

    submit_uc = SubmitTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        dispatcher=dispatcher,
    )

    sub_res = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="direct-dispatch-idemp-1",
        )
    )
    assert sub_res.job_id is not None

    # Job was synchronously processed by dispatcher
    async with tryon_uow:
        processed_job = await tryon_uow.jobs.get_by_id(sub_res.job_id)
        assert processed_job.status == "completed"


@pytest.mark.asyncio
async def test_idempotent_submit_and_cache_hit(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    """MVP 4.4: Idempotent repeat submission returns existing job and composite cache hit."""
    storage = LocalStorage(tmp_path)
    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()

    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    portrait_bytes = _create_valid_portrait_bytes()
    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=portrait_bytes,
        )
    )
    assert photo_res.status == "accepted"

    garment_img_key = f"catalog/garments/{garment_id}_cached.jpg"
    garment_bytes = _create_valid_portrait_bytes()
    storage.put(garment_img_key, garment_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="White Linen Shirt",
            category="tops",
            subcategory="shirts",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=500000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_img_key,
            content_hash=hashlib.sha256(garment_bytes).hexdigest(),
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(img)
        await catalog_uow.commit()

    worker = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        storage=storage,
    )
    dispatcher = DirectTryOnJobDispatcher(worker)

    submit_uc = SubmitTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        dispatcher=dispatcher,
    )

    # First submission -> processes and creates artifact
    res1 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="idemp-cache-test",
        )
    )
    assert res1.job_id is not None

    # Repeat submission with same idempotency key -> returns completed cached job
    res2 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="idemp-cache-test",
        )
    )
    assert res2.job_id == res1.job_id
    assert res2.is_cached is True
    assert res2.status == "completed"

    # Second submission with DIFFERENT idempotency key -> composite cache hit on artifact!
    res3 = await submit_uc.execute(
        SubmitTryOnJobCommand(
            user_id=user_id,
            garment_id=garment_id,
            idempotency_key="idemp-cache-different",
        )
    )
    assert res3.is_cached is True
    assert res3.status == "completed"
    assert res3.artifact_key == res1.artifact_key


@pytest.mark.asyncio
async def test_worker_bootstrap_run_tryon_job(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
    tmp_path,
) -> None:
    """MVP 4.3: Worker entrypoint run_tryon_job executes successfully."""
    import fashx.workers.app as workers_app
    from fashx.workers.app import run_tryon_job

    storage = LocalStorage(tmp_path)
    monkeypatch.setattr(workers_app, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(workers_app, "get_storage", lambda: storage)

    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    user_id = uuid4()
    garment_id = uuid4()
    job_id = uuid4()

    create_uc = CreateProfileUseCase(profile_uow)
    await create_uc.execute(
        CreateProfileCommand(
            user_id=user_id,
            height_cm=180,
            weight_kg=75,
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)],
        )
    )

    portrait_bytes = _create_valid_portrait_bytes()
    upload_uc = UploadUserPhotoUseCase(profile_uow, storage=storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=portrait_bytes,
        )
    )

    garment_img_key = f"catalog/garments/{garment_id}_worker.jpg"
    storage.put(garment_img_key, portrait_bytes)

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Worker Blue Tee",
            category="tops",
            subcategory="t-shirt",
            gender="unisex",
            active=True,
            in_stock=True,
            price_minor=200000,
            tryon_supported=True,
            version=1,
        )
        catalog_uow.canonical_garments.add(garment)
        img = GarmentImage(
            id=uuid4(),
            garment_id=garment_id,
            storage_key=garment_img_key,
            content_hash=hashlib.sha256(portrait_bytes).hexdigest(),
            image_type="primary",
            version=1,
        )
        catalog_uow.images.add(img)
        await catalog_uow.commit()

    art_key = f"art-{job_id}"
    async with tryon_uow:
        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_res.photo_id,
            idempotency_key=f"idemp-{job_id}",
            artifact_key=art_key,
            status="queued",
            model_version="tryon-v1.6",
            pipeline_version="pilot-pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

    # Invoke run_tryon_job worker entrypoint
    result = run_tryon_job(job_id)
    assert result.status == "completed"
    assert result.result_url is not None

