import io
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.revoke_consent import (
    RevokeConsentCommand,
    RevokeConsentUseCase,
)
from fashx.profile.application.upload_photo import (
    UploadPhotoCommand,
    UploadUserPhotoUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from database.models.tryon import TryOnArtifact, TryOnJob


def _create_portrait_image() -> bytes:
    img = Image.new("RGB", (600, 800), (140, 120, 100))
    for x in range(300):
        for y in range(800):
            img.putpixel((x, y), (80, 60, 40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_consent_revocation_cascades_hard_deletion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    tryon_uow = TryOnUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # 1. Create User with body_photo consent
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(
        CreateProfileCommand(
            height_cm=180,
            weight_kg=75,
            consents={"body_photo": True},
        )
    )
    user_id = user_res.user_id

    # 2. Upload Photo (Stored in Storage and DB)
    upload_uc = UploadUserPhotoUseCase(profile_uow, storage)
    photo_res = await upload_uc.execute(
        UploadPhotoCommand(
            user_id=user_id,
            photo_type="tryon_reference",
            photo_bytes=_create_portrait_image(),
        )
    )
    assert photo_res.status == "accepted"
    assert photo_res.storage_key is not None
    photo_key = photo_res.storage_key
    assert await storage.exists(photo_key) is True

    # 3. Simulate TryOn Job and Artifact linked to this photo
    dummy_garment_id = uuid4()
    async with tryon_uow:
        job = TryOnJob(
            user_id=user_id,
            garment_id=dummy_garment_id,
            profile_photo_id=photo_res.photo_id,
            idempotency_key="idemp-test-purge",
            artifact_key="cache-key-purge-test",
            status="completed",
            model_version="mock-v1",
            pipeline_version="pipe-v1",
        )
        tryon_uow.jobs.add(job)
        await tryon_uow.commit()

        artifact = TryOnArtifact(
            job_id=job.id,
            artifact_key=job.artifact_key,
            result_key="s3://tryon-artifacts/test.png",
            model_version="mock-v1",
            pipeline_version="pipe-v1",
            photo_version=1,
            garment_version=1,
        )
        tryon_uow.artifacts.add(artifact)
        await tryon_uow.commit()

    # Verify Job and Artifact Exist
    async with tryon_uow:
        jobs_before = await tryon_uow.jobs.list_by_user(user_id)
        assert len(jobs_before) == 1

    # 4. User Revokes Consent for 'body_photo' (Rule I16 & Gate G4)
    revoke_uc = RevokeConsentUseCase(profile_uow, tryon_uow, storage)
    revoke_res = await revoke_uc.execute(
        RevokeConsentCommand(user_id=user_id, data_type="body_photo")
    )

    assert revoke_res.status == "revoked_and_purged"
    assert revoke_res.photos_purged == 1
    assert revoke_res.jobs_purged == 1

    # 5. Verify Zero Residual Data Across Storage and Database (Gate G4)
    # Storage check: File purged
    assert await storage.exists(photo_key) is False

    # Database check: Zero photos
    async with profile_uow:
        photos_after = await profile_uow.photos.list_for_user(user_id)
        assert len(photos_after) == 0

        # Consent record set to False
        has_consent = await profile_uow.consents.has_consent(user_id, "body_photo")
        assert has_consent is False

    # Database check: Zero tryon jobs
    async with tryon_uow:
        jobs_after = await tryon_uow.jobs.list_by_user(user_id)
        assert len(jobs_after) == 0
