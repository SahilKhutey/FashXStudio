from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import Base
from database.models.catalog import CanonicalGarment
from database.models.identity import User, UserPhoto
from database.models.media import MediaObject
from database.models.tryon import TryOnArtifact, TryOnJob
from fashx.infrastructure.storage.local import LocalStorage
from fashx.profile.application.delete_photo import delete_user_photo


@pytest.mark.asyncio
async def test_single_photo_deletion_cascades_jobs_and_purges_result_media(tmp_path) -> None:
    """Design decision: Derived try-on data dies with its source photo.

    When photo_1 is deleted:
      - photo_1 is deleted from DB and storage
      - job_1 (derived from photo_1) is cascaded from DB
      - job_1 result media row in media_objects is deleted
      - job_1 result files in storage are deleted
      - photo_2 and its derived job_2 and media remain completely untouched
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
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
        # Seed parent user and garment
        session.add(User(id=user_id))
        session.add(CanonicalGarment(id=garment_id, display_name="Top", category="tops"))
        await session.flush()

        # Seed photos
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

        # Seed media_objects for photos
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
        await session.flush()

        # Seed jobs and artifacts for photo 1
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

        # Seed jobs and artifacts for photo 2
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
        session.add_all([job1, job2])
        await session.flush()
        session.add_all([art1, art2, m_j1, m_j2])
        await session.flush()

        await session.commit()

    # Pre-condition assertions
    assert storage.exists(p1_key)
    assert storage.exists(p2_key)
    assert storage.exists(j1_art_key)
    assert storage.exists(j1_res_key)
    assert storage.exists(j2_art_key)
    assert storage.exists(j2_res_key)

    # Perform single-photo deletion on photo 1
    async with session_factory() as session:
        deleted = await delete_user_photo(
            session,
            user_id=user_id,
            photo_id=p1_id,
            storage=storage,
        )
        assert deleted is True
        await session.commit()

    # Verification: Photo 1, Job 1, Artifact 1, and Result Media 1 are purged
    async with session_factory() as session:
        remaining_photos = (await session.scalars(select(UserPhoto))).all()
        assert len(remaining_photos) == 1
        assert remaining_photos[0].id == p2_id, "Photo 2 must remain untouched"

        remaining_jobs = (await session.scalars(select(TryOnJob))).all()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == j2_id, "Job 2 must remain untouched"
        assert remaining_jobs[0].profile_photo_id == p2_id

        remaining_artifacts = (await session.scalars(select(TryOnArtifact))).all()
        assert len(remaining_artifacts) == 1
        assert remaining_artifacts[0].job_id == j2_id, "Artifact 2 must remain untouched"

        remaining_media = (await session.scalars(select(MediaObject))).all()
        remaining_media_keys = {m.object_key for m in remaining_media}
        assert p1_key not in remaining_media_keys, "Photo 1 media object must be deleted"
        assert j1_res_key not in remaining_media_keys, "Job 1 result media object must be deleted"
        assert p2_key in remaining_media_keys, "Photo 2 media object must be preserved"
        assert j2_res_key in remaining_media_keys, "Job 2 result media object must be preserved"

    # Verification: Storage objects purged for photo 1 and job 1, preserved for photo 2 and job 2
    assert not storage.exists(p1_key), "Photo 1 file must be deleted from storage"
    assert not storage.exists(j1_art_key), "Job 1 artifact file must be deleted from storage"
    assert not storage.exists(j1_res_key), "Job 1 result file must be deleted from storage"

    assert storage.exists(p2_key), "Photo 2 file must be preserved in storage"
    assert storage.exists(j2_art_key), "Job 2 artifact file must be preserved in storage"
    assert storage.exists(j2_res_key), "Job 2 result file must be preserved in storage"


@pytest.mark.asyncio
async def test_delete_photo_endpoint_api(tmp_path) -> None:
    """Verify DELETE /api/v1/profile/{user_id}/photos/{photo_id} HTTP endpoint."""
    from fashx.core.errors import EntityNotFoundError
    from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
    from fashx.profile.router import delete_photo_endpoint
    from fashx.security.deps import Principal
    from fashx.security.errors import ApiError

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    storage = LocalStorage(tmp_path)

    user_id = uuid4()
    other_user_id = uuid4()
    p_id = uuid4()
    p_key = f"u/{user_id}/photos/{p_id}.jpg"
    storage.put(p_key, b"bytes", "image/jpeg")

    async with session_factory() as session:
        session.add(User(id=user_id))
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

    # 1. User ID mismatch raises 403 Forbidden
    with pytest.raises(ApiError) as exc:
        await delete_photo_endpoint(
            user_id=user_id,
            photo_id=p_id,
            principal=Principal(user_id=str(other_user_id), subject=str(other_user_id), roles=frozenset({"customer"})),
            uow=uow,
            storage=storage,
        )
    assert exc.value.status == 403

    # 2. Deleting photo with matching principal succeeds
    await delete_photo_endpoint(
        user_id=user_id,
        photo_id=p_id,
        principal=Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"})),
        uow=uow,
        storage=storage,
    )

    # Assert photo row and storage key are gone
    async with session_factory() as session:
        photo = (await session.scalars(select(UserPhoto).where(UserPhoto.id == p_id))).first()
        assert photo is None
    assert not storage.exists(p_key)

    # 3. Repeated delete raises 404 EntityNotFoundError
    with pytest.raises(EntityNotFoundError):
        await delete_photo_endpoint(
            user_id=user_id,
            photo_id=p_id,
            principal=Principal(user_id=str(user_id), subject=str(user_id), roles=frozenset({"customer"})),
            uow=uow,
            storage=storage,
        )

