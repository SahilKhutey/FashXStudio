import io

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.core.errors import ConsentRequiredError
from api.app.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.upload_photo import (
    UploadPhotoCommand,
    UploadUserPhotoUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from schemas.common.enums import DataType, PhotoStatus, PhotoType
from schemas.identity.consent import ConsentUpdate


def create_portrait(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    img = Image.new("RGB", (width, height), color)
    for x in range(width // 2):
        for y in range(height):
            img.putpixel(
                (x, y), (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
            )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_photo_without_consent_raises(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # User created WITHOUT body_photo consent
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(CreateProfileCommand())

    photo_bytes = create_portrait(600, 800, (150, 120, 100))
    upload_uc = UploadUserPhotoUseCase(uow, storage)

    cmd = UploadPhotoCommand(
        user_id=profile.user_id,
        photo_type=PhotoType.TRYON_REFERENCE,
        photo_bytes=photo_bytes,
    )

    with pytest.raises(ConsentRequiredError) as exc_info:
        await upload_uc.execute(cmd)
    assert exc_info.value.data_type == DataType.BODY_PHOTO.value


@pytest.mark.asyncio
async def test_upload_photo_dark_fails_quality_gate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # User created WITH body_photo consent
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )

    # Very dark image
    dark_bytes = create_portrait(600, 800, (20, 20, 20))
    upload_uc = UploadUserPhotoUseCase(uow, storage)

    cmd = UploadPhotoCommand(
        user_id=profile.user_id,
        photo_type=PhotoType.TRYON_REFERENCE,
        photo_bytes=dark_bytes,
    )
    result = await upload_uc.execute(cmd)

    assert result.status == PhotoStatus.REJECTED.value
    assert result.storage_key is None
    assert "too dark" in result.reject_reason.lower()

    # Storage should be untouched
    assert len(storage._objects) == 0


@pytest.mark.asyncio
async def test_upload_photo_clean_passes_and_calibrates(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)])
    )

    # Valid, balanced portrait
    valid_bytes = create_portrait(600, 800, (160, 130, 95))
    upload_uc = UploadUserPhotoUseCase(uow, storage)

    cmd = UploadPhotoCommand(
        user_id=profile.user_id,
        photo_type=PhotoType.TRYON_REFERENCE,
        photo_bytes=valid_bytes,
    )
    result = await upload_uc.execute(cmd)

    assert result.status == PhotoStatus.ACCEPTED.value
    assert result.storage_key is not None
    assert result.reject_reason is None
    assert result.skin_tone is not None
    assert result.skin_tone.monk_scale_index in range(1, 11)

    # Stored in object storage
    assert await storage.exists(result.storage_key)
