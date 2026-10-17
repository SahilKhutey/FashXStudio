from __future__ import annotations

import io
from uuid import uuid4

import pytest
import pytest_asyncio
from PIL import Image
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, StyleQuizPick
from database.models.commerce_feedback import WardrobeItem
from database.models.identity import ConsentRecord, User, UserPhoto
from database.models.media import MediaObject
from database.models.operations import OutboxMessageRecord
from database.models.profile import OnboardingProfile
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.api.v1.me import get_me
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.infrastructure.storage.local import LocalStorage
from fashx.integration.outbox import run_outbox_worker_once
from fashx.profile.application.delete_photo import delete_user_photo
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.profile.router import delete_photo_endpoint
from fashx.security.deps import Principal
from fashx.security.errors import ApiError
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.ports import InferenceInput, InferenceOutput
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


def _create_valid_portrait_bytes() -> bytes:
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


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_single_photo_deletion_cascades_jobs_and_purges_storage_via_outbox(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """Outbox-backed storage purge and cascading deletion:

    When photo_1 is deleted:
      - photo_1 is deleted from DB
      - job_1 (derived from photo_1) cascades from DB
      - artifact_1 cascades from DB
      - media objects for photo_1 and job_1 are deleted from DB
      - outbox record for storage.delete_keys is added in the same transaction
      - files remain in storage until the outbox worker processes them
      - after running outbox worker, photo_1 and job_1 files are deleted
      - photo_2 and job_2 remain completely untouched in DB and storage
    """
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    garment_id = uuid4()

    p1_id = uuid4()
    p2_id = uuid4()
    p1_key = f"u/{user_id}/photos/{p1_id}.jpg"
    p2_key = f"u/{user_id}/photos/{p2_id}.jpg"

    j1_id = uuid4()
    j2_id = uuid4()
    j1_art_key = f"u/{user_id}/tryon/{j1_id}_art.jpg"
    j1_res_key = f"u/{user_id}/tryon/{j1_id}_res.jpg"
    j2_art_key = f"u/{user_id}/tryon/{j2_id}_art.jpg"
    j2_res_key = f"u/{user_id}/tryon/{j2_id}_res.jpg"

    # Put files in storage
    storage.put(p1_key, b"photo_1_bytes", "image/jpeg")
    storage.put(p2_key, b"photo_2_bytes", "image/jpeg")
    storage.put(j1_art_key, b"job_1_art", "image/jpeg")
    storage.put(j1_res_key, b"job_1_res", "image/jpeg")
    storage.put(j2_art_key, b"job_2_art", "image/jpeg")
    storage.put(j2_res_key, b"job_2_res", "image/jpeg")

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(CanonicalGarment(id=garment_id, display_name="Top", category="tops"))
        await session.flush()

        photo1 = UserPhoto(
            id=p1_id,
            user_id=user_id,
            photo_type="body",
            storage_key=p1_key,
            status="accepted",
        )
        photo2 = UserPhoto(
            id=p2_id,
            user_id=user_id,
            photo_type="body",
            storage_key=p2_key,
            status="accepted",
        )
        session.add_all([photo1, photo2])

        m_p1 = MediaObject(
            id=p1_id,
            user_id=user_id,
            kind="reference_photo",
            object_key=p1_key,
            sha256="a" * 64,
            size_bytes=100,
            content_type="image/jpeg",
        )
        m_p2 = MediaObject(
            id=p2_id,
            user_id=user_id,
            kind="reference_photo",
            object_key=p2_key,
            sha256="b" * 64,
            size_bytes=100,
            content_type="image/jpeg",
        )
        session.add_all([m_p1, m_p2])

        job1 = TryOnJob(
            id=j1_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=p1_id,
            idempotency_key="k1",
            artifact_key=j1_art_key,
            model_version="1.0",
            pipeline_version="1.0",
        )
        job2 = TryOnJob(
            id=j2_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=p2_id,
            idempotency_key="k2",
            artifact_key=j2_art_key,
            model_version="1.0",
            pipeline_version="1.0",
        )
        session.add_all([job1, job2])
        await session.flush()

        art1 = TryOnArtifact(
            id=uuid4(),
            job_id=j1_id,
            artifact_key=j1_art_key,
            result_key=j1_res_key,
            model_version="1.0",
            pipeline_version="1.0",
            photo_version=1,
            garment_version=1,
        )
        m_j1 = MediaObject(
            id=uuid4(),
            user_id=user_id,
            kind="tryon_result",
            object_key=j1_res_key,
            sha256="c" * 64,
            size_bytes=200,
            content_type="image/jpeg",
        )
        art2 = TryOnArtifact(
            id=uuid4(),
            job_id=j2_id,
            artifact_key=j2_art_key,
            result_key=j2_res_key,
            model_version="1.0",
            pipeline_version="1.0",
            photo_version=1,
            garment_version=1,
        )
        m_j2 = MediaObject(
            id=uuid4(),
            user_id=user_id,
            kind="tryon_result",
            object_key=j2_res_key,
            sha256="d" * 64,
            size_bytes=200,
            content_type="image/jpeg",
        )

        session.add_all([art1, art2, m_j1, m_j2])
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)

    # 1. Perform deletion of photo 1 via delete_user_photo
    async with uow:
        await delete_user_photo(uow, user_id=user_id, photo_id=p1_id)
        await uow.commit()

    # 2. Verify DB state: Photo 1, Job 1, Artifact 1, and Media 1 are removed; Photo 2 is untouched
    async with session_factory() as session:
        remaining_photos = (await session.scalars(select(UserPhoto))).all()
        assert len(remaining_photos) == 1
        assert remaining_photos[0].id == p2_id

        remaining_jobs = (await session.scalars(select(TryOnJob))).all()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == j2_id

        remaining_artifacts = (await session.scalars(select(TryOnArtifact))).all()
        assert len(remaining_artifacts) == 1
        assert remaining_artifacts[0].job_id == j2_id

        remaining_media = (await session.scalars(select(MediaObject))).all()
        remaining_media_keys = {m.object_key for m in remaining_media}
        assert p1_key not in remaining_media_keys
        assert j1_res_key not in remaining_media_keys
        assert p2_key in remaining_media_keys
        assert j2_res_key in remaining_media_keys

        # Check outbox has the purge task queued (not yet published)
        outbox_msgs = (await session.scalars(select(OutboxMessageRecord))).all()
        assert len(outbox_msgs) == 1
        assert outbox_msgs[0].topic == "storage.delete_keys"
        assert outbox_msgs[0].published_at is None
        keys_in_payload = set(outbox_msgs[0].payload.get("keys", []))
        assert p1_key in keys_in_payload
        assert j1_art_key in keys_in_payload
        assert j1_res_key in keys_in_payload

    # 3. Verify storage state BEFORE worker runs: files still exist because purge is asynchronous
    assert storage.exists(p1_key), "Storage files must remain intact until outbox worker processes them"
    assert storage.exists(j1_art_key)
    assert storage.exists(j1_res_key)
    assert storage.exists(p2_key)

    # 4. Run outbox worker to execute the purge
    async with uow:
        processed = await run_outbox_worker_once(uow, storage)
        await uow.commit()
    assert processed == 1

    # 5. Verify storage state AFTER worker runs
    assert not storage.exists(p1_key), "Photo 1 file must be deleted by worker"
    assert not storage.exists(j1_art_key), "Job 1 artifact file must be deleted by worker"
    assert not storage.exists(j1_res_key), "Job 1 result file must be deleted by worker"

    assert storage.exists(p2_key), "Photo 2 file must remain untouched"
    assert storage.exists(j2_art_key), "Job 2 artifact file must remain untouched"
    assert storage.exists(j2_res_key), "Job 2 result file must remain untouched"

    # Outbox message should now be published
    async with session_factory() as session:
        msg = (await session.scalars(select(OutboxMessageRecord))).first()
        assert msg is not None
        assert msg.published_at is not None


@pytest.mark.asyncio
async def test_delete_photo_cross_user_returns_404(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """Verifies that attempting to delete an unowned photo or non-existent photo returns 404 not_found."""
    storage = LocalStorage(tmp_path)

    user_a = uuid4()
    user_b = uuid4()
    p_a = uuid4()
    p_a_key = f"u/{user_a}/photos/{p_a}.jpg"
    storage.put(p_a_key, b"bytes_a", "image/jpeg")

    async with session_factory() as session:
        session.add_all([User(id=user_a), User(id=user_b)])
        await session.flush()
        photo = UserPhoto(
            id=p_a,
            user_id=user_a,
            photo_type="body",
            storage_key=p_a_key,
            status="accepted",
        )
        session.add(photo)
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)

    # 1. User B tries to delete User A's photo -> 404 not_found
    with pytest.raises(ApiError) as exc_info:
        async with uow:
            await delete_user_photo(uow, user_id=user_b, photo_id=p_a)
    assert exc_info.value.status == 404
    assert exc_info.value.code == "not_found"

    # 2. User A tries to delete non-existent photo -> 404 not_found
    with pytest.raises(ApiError) as exc_info2:
        async with uow:
            await delete_user_photo(uow, user_id=user_a, photo_id=uuid4())
    assert exc_info2.value.status == 404
    assert exc_info2.value.code == "not_found"

    # 3. Assert User A's photo remains intact in DB and storage
    async with session_factory() as session:
        photo_db = (await session.scalars(select(UserPhoto).where(UserPhoto.id == p_a))).first()
        assert photo_db is not None
        outbox_count = (await session.scalars(select(OutboxMessageRecord))).all()
        assert len(outbox_count) == 0

    assert storage.exists(p_a_key)


@pytest.mark.asyncio
async def test_photo_deletion_keeps_closet_item_but_drops_render(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """When a photo is deleted and its tryon jobs/artifacts cascade, wardrobe/closet

    items built from those jobs must remain with snapshot_title and price intact,
    while tryon_artifact_id is set to NULL.
    """
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()
    job_id = uuid4()
    art_id = uuid4()
    wardrobe_id = uuid4()

    photo_key = f"u/{user_id}/photos/{photo_id}.jpg"
    art_key = f"u/{user_id}/tryon/{job_id}_art.jpg"
    res_key = f"u/{user_id}/tryon/{job_id}_res.jpg"

    storage.put(photo_key, b"photo", "image/jpeg")
    storage.put(art_key, b"art", "image/jpeg")
    storage.put(res_key, b"res", "image/jpeg")

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(CanonicalGarment(id=garment_id, display_name="Silk Blouse", category="tops"))
        await session.flush()

        session.add(
            UserPhoto(
                id=photo_id,
                user_id=user_id,
                photo_type="body",
                storage_key=photo_key,
                status="accepted",
            )
        )
        await session.flush()

        session.add(
            TryOnJob(
                id=job_id,
                user_id=user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_wardrobe",
                artifact_key=art_key,
                model_version="1.0",
                pipeline_version="1.0",
            )
        )
        await session.flush()

        session.add(
            TryOnArtifact(
                id=art_id,
                job_id=job_id,
                artifact_key=art_key,
                result_key=res_key,
                model_version="1.0",
                pipeline_version="1.0",
                photo_version=1,
                garment_version=1,
            )
        )
        await session.flush()

        session.add(
            WardrobeItem(
                id=wardrobe_id,
                user_id=user_id,
                garment_id=garment_id,
                tryon_artifact_id=art_id,
                snapshot_title="Silk Blouse",
                snapshot_price_minor=4999,
                snapshot_currency="INR",
                snapshot_image_key=res_key,
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)

    # Delete photo
    async with uow:
        await delete_user_photo(uow, user_id=user_id, photo_id=photo_id)
        await uow.commit()

    # Verify WardrobeItem survived with intact metadata and NULL tryon_artifact_id
    async with session_factory() as session:
        item = (await session.scalars(select(WardrobeItem).where(WardrobeItem.id == wardrobe_id))).first()
        assert item is not None, "WardrobeItem must survive photo deletion"
        assert item.snapshot_title == "Silk Blouse"
        assert item.snapshot_price_minor == 4999
        assert item.snapshot_currency == "INR"
        assert item.snapshot_image_key == res_key
        assert item.tryon_artifact_id is None, "tryon_artifact_id must be set to NULL via ON DELETE SET NULL"

        # Verify Job and Artifact are gone
        job = (await session.scalars(select(TryOnJob).where(TryOnJob.id == job_id))).first()
        assert job is None
        art = (await session.scalars(select(TryOnArtifact).where(TryOnArtifact.id == art_id))).first()
        assert art is None

    # Run outbox worker to purge the result image
    async with uow:
        await run_outbox_worker_once(uow, storage)
        await uow.commit()

    assert not storage.exists(res_key), "Rendered try-on result must be purged from storage"


@pytest.mark.asyncio
async def test_in_flight_tryon_discarded_when_photo_deleted(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """If a photo is deleted while an external try-on job is mid-flight, the worker

    must detect that the job was cascaded/deleted and discard incoming vendor outputs
    without creating an artifact or writing to storage.
    """
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()
    job_id = uuid4()
    art_key = f"u/{user_id}/tryon/{job_id}_art.jpg"
    photo_key = f"u/{user_id}/photos/{photo_id}.jpg"

    storage.put(photo_key, b"photo_bytes", "image/jpeg")

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(CanonicalGarment(id=garment_id, display_name="T-Shirt", category="tops"))
        await session.flush()

        session.add(
            ConsentRecord(
                user_id=user_id,
                data_type="body_photo",
                granted=True,
                is_18_or_older=True,
                consent_version="2026.1",
            )
        )
        session.add(
            UserPhoto(
                id=photo_id,
                user_id=user_id,
                photo_type="body",
                storage_key=photo_key,
                status="accepted",
            )
        )
        await session.flush()

        session.add(
            TryOnJob(
                id=job_id,
                user_id=user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_midflight",
                artifact_key=art_key,
                status="queued",
                model_version="1.0",
                pipeline_version="1.0",
            )
        )
        await session.commit()

    valid_portrait_bytes = _create_valid_portrait_bytes()

    # Custom adapter simulating photo deletion during long vendor inference
    class MidFlightDeletionAdapter:
        def __init__(self, factory: async_sessionmaker[AsyncSession], u_id: uuid4, p_id: uuid4):
            self.factory = factory
            self.u_id = u_id
            self.p_id = p_id

        async def execute_tryon(self, inference_input: InferenceInput) -> InferenceOutput:
            # Simulate photo deletion happening while vendor is computing
            uow_del = ProfileUnitOfWork(self.factory)
            async with uow_del:
                await delete_user_photo(uow_del, user_id=self.u_id, photo_id=self.p_id)
                await uow_del.commit()

            return InferenceOutput(
                rendered_image_bytes=valid_portrait_bytes,
                model_version="1.0",
                pipeline_version="1.0",
                inference_latency_ms=350.0,
            )

    tryon_uow = TryOnUnitOfWork(session_factory)
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)

    adapter = MidFlightDeletionAdapter(session_factory, user_id, photo_id)
    process_uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=adapter,
        storage=storage,
    )

    result = await process_uc.execute(
        job_id=job_id,
        user_photo_bytes=valid_portrait_bytes,
        garment_image_bytes=valid_portrait_bytes,
    )

    # Worker detects job cancellation / deletion
    assert result.status == "cancelled"
    assert result.failure_reason == "job_deleted"

    # Assert no artifact row exists
    async with session_factory() as session:
        artifacts = (await session.scalars(select(TryOnArtifact))).all()
        assert len(artifacts) == 0

    # Assert no tryon result file is stored in storage
    result_key = f"u/{user_id}/tryon_result/{job_id}"
    assert not storage.exists(result_key)


@pytest.mark.asyncio
async def test_onboarding_missing_photo_after_deleting_last_photo(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """Deleting the last accepted photo sets onboarding.missing == ['photo'] in GET /me."""
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    photo_id = uuid4()
    photo_key = f"u/{user_id}/photos/{photo_id}.jpg"
    storage.put(photo_key, b"bytes", "image/jpeg")

    g1, g2, g3 = uuid4(), uuid4(), uuid4()

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add_all(
            [
                CanonicalGarment(id=g1, display_name="G1", category="tops"),
                CanonicalGarment(id=g2, display_name="G2", category="tops"),
                CanonicalGarment(id=g3, display_name="G3", category="tops"),
            ]
        )
        await session.flush()

        # Consents: terms_and_privacy and body_photo
        session.add(
            ConsentRecord(
                user_id=user_id,
                data_type="terms_and_privacy",
                granted=True,
                is_18_or_older=True,
                consent_version="2026.1",
            )
        )
        session.add(
            ConsentRecord(
                user_id=user_id,
                data_type="body_photo",
                granted=True,
                is_18_or_older=True,
                consent_version="2026.1",
            )
        )
        # Completed onboarding profile
        session.add(OnboardingProfile(user_id=user_id, status="completed"))
        # 3 Style quiz picks
        session.add_all(
            [
                StyleQuizPick(id=uuid4(), user_id=user_id, garment_id=g1, liked=True),
                StyleQuizPick(id=uuid4(), user_id=user_id, garment_id=g2, liked=True),
                StyleQuizPick(id=uuid4(), user_id=user_id, garment_id=g3, liked=True),
            ]
        )
        # 1 Accepted photo
        session.add(
            UserPhoto(
                id=photo_id,
                user_id=user_id,
                photo_type="body",
                storage_key=photo_key,
                status="accepted",
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)
    principal = Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"}))

    # Pre-condition: Onboarding is completely finished
    me_resp = await get_me(principal=principal, profile_uow=uow)
    assert me_resp.onboarding.complete is True
    assert me_resp.onboarding.missing == []

    # Action: Delete the photo
    async with uow:
        await delete_user_photo(uow, user_id=user_id, photo_id=photo_id)
        await uow.commit()

    # Post-condition: GET /me reports onboarding incomplete, missing only ["photo"]
    me_resp_after = await get_me(principal=principal, profile_uow=uow)
    assert me_resp_after.onboarding.complete is False
    assert me_resp_after.onboarding.missing == ["photo"]


@pytest.mark.asyncio
async def test_keys_derived_from_photo_is_complete(
    session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Verifies that MediaRepository.keys_derived_from_photo returns a complete

    list of all objects linked to the photo (source, thumbnail/copies, job artifacts, and results).
    """
    user_id = uuid4()
    photo_id = uuid4()
    job_id = uuid4()
    garment_id = uuid4()

    photo_key = f"u/{user_id}/photos/{photo_id}.jpg"
    thumb_key = f"u/{user_id}/photos/{photo_id}_thumb.jpg"
    art_key = f"u/{user_id}/tryon/{job_id}_art.jpg"
    res_key = f"u/{user_id}/tryon/{job_id}_res.jpg"

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(CanonicalGarment(id=garment_id, display_name="Dress", category="dresses"))
        await session.flush()

        session.add(
            UserPhoto(
                id=photo_id,
                user_id=user_id,
                photo_type="body",
                storage_key=photo_key,
                status="accepted",
            )
        )
        session.add(
            MediaObject(
                id=uuid4(),
                user_id=user_id,
                kind="reference_photo",
                object_key=thumb_key,
                sha256="1" * 64,
                size_bytes=50,
                content_type="image/jpeg",
            )
        )
        session.add(
            TryOnJob(
                id=job_id,
                user_id=user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key="idemp_keys",
                artifact_key=art_key,
                model_version="1.0",
                pipeline_version="1.0",
            )
        )
        await session.flush()

        session.add(
            TryOnArtifact(
                id=uuid4(),
                job_id=job_id,
                artifact_key=art_key,
                result_key=res_key,
                model_version="1.0",
                pipeline_version="1.0",
                photo_version=1,
                garment_version=1,
            )
        )
        session.add(
            MediaObject(
                id=uuid4(),
                user_id=user_id,
                kind="tryon_result",
                object_key=res_key,
                sha256="2" * 64,
                size_bytes=200,
                content_type="image/jpeg",
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)
    async with uow:
        keys = await uow.media.keys_derived_from_photo(photo_id)

    expected = sorted([photo_key, thumb_key, art_key, res_key])
    assert keys == expected


@pytest.mark.asyncio
async def test_delete_photo_endpoint_api(
    session_factory: async_sessionmaker[AsyncSession], tmp_path
) -> None:
    """Verify DELETE /api/v1/profile/{user_id}/photos/{photo_id} HTTP endpoint."""
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    other_user_id = uuid4()
    p_id = uuid4()
    p_key = f"u/{user_id}/photos/{p_id}.jpg"
    storage.put(p_key, b"bytes", "image/jpeg")

    async with session_factory() as session:
        session.add(User(id=user_id))
        session.add(User(id=other_user_id))
        await session.flush()
        session.add(
            UserPhoto(
                id=p_id,
                user_id=user_id,
                photo_type="body",
                storage_key=p_key,
                status="accepted",
            )
        )
        await session.commit()

    uow = ProfileUnitOfWork(session_factory)

    # 1. User ID mismatch in path vs principal raises 403 Forbidden
    with pytest.raises(ApiError) as exc:
        await delete_photo_endpoint(
            user_id=user_id,
            photo_id=p_id,
            principal=Principal(user_id=str(other_user_id), subject=str(other_user_id), roles=frozenset({"customer"})),
            uow=uow,
        )
    assert exc.value.status == 403

    # 2. Deleting photo with matching principal succeeds (returns None / HTTP 204)
    res = await delete_photo_endpoint(
        user_id=user_id,
        photo_id=p_id,
        principal=Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"})),
        uow=uow,
    )
    assert res is None

    # Assert photo row is gone from DB
    async with session_factory() as session:
        photo = (await session.scalars(select(UserPhoto).where(UserPhoto.id == p_id))).first()
        assert photo is None

        # Outbox message was staged
        outbox_msgs = (await session.scalars(select(OutboxMessageRecord))).all()
        assert len(outbox_msgs) == 1
        assert outbox_msgs[0].topic == "storage.delete_keys"

    # 3. Repeated delete raises 404 not_found
    with pytest.raises(ApiError) as exc_404:
        await delete_photo_endpoint(
            user_id=user_id,
            photo_id=p_id,
            principal=Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"})),
            uow=uow,
        )
    assert exc_404.value.status == 404
    assert exc_404.value.code == "not_found"
