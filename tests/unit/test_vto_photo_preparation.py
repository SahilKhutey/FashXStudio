from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.core.errors import ConsentRequiredError
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.application.prepare_user_photo import (
    PrepareUserPhotoCommand,
    UserPhotoUploadService,
)
from fashx.profile.images.detector import (
    MockPersonDetector,
)
from fashx.profile.images.prepare_photo import (
    PersonPhotoPreparer,
    PhotoPreparationError,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from schemas.common.enums import DataType, PhotoStatus, PhotoType
from schemas.identity.consent import ConsentUpdate


def make_test_photo(
    width: int,
    height: int,
    color: tuple[int, int, int] = (150, 120, 100),
    add_gradient: bool = True,
    format_: str = "PNG",
) -> bytes:
    img = Image.new("RGB", (width, height), color)
    if add_gradient:
        for x in range(width // 2):
            for y in range(height):
                img.putpixel(
                    (x, y),
                    (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50)),
                )
    buf = io.BytesIO()
    img.save(buf, format=format_)
    return buf.getvalue()


def test_preparer_normalizes_png_to_jpeg_and_computes_sha256() -> None:
    raw_png = make_test_photo(600, 800, color=(160, 130, 105))
    preparer = PersonPhotoPreparer(detector=MockPersonDetector(person_count=1))
    prepared = preparer.prepare(raw_png)

    assert prepared.image_format == "JPEG"
    assert prepared.width == 600
    assert prepared.height == 800
    assert prepared.file_size_bytes == len(prepared.image_bytes)
    assert prepared.content_sha256 == hashlib.sha256(prepared.image_bytes).hexdigest()
    assert prepared.has_person is True
    assert prepared.has_face is True
    assert prepared.ready_for_tryon is True
    assert prepared.quality_score > 0.5


def test_preparer_composites_rgba_with_white_background() -> None:
    img = Image.new("RGBA", (600, 800), (160, 130, 105, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_rgba = buf.getvalue()

    preparer = PersonPhotoPreparer(detector=MockPersonDetector(person_count=1))
    prepared = preparer.prepare(raw_rgba)

    assert prepared.image_format == "JPEG"
    assert prepared.width == 600
    assert prepared.height == 800
    assert prepared.ready_for_tryon is True


def test_preparer_downscales_oversized_images() -> None:
    raw_large = make_test_photo(2000, 3000, color=(150, 120, 100))
    preparer = PersonPhotoPreparer(max_output_side=1536, detector=MockPersonDetector(person_count=1))
    prepared = preparer.prepare(raw_large)

    assert prepared.height == 1536
    assert prepared.width == int(round(2000 * (1536 / 3000)))
    assert prepared.ready_for_tryon is True


def test_preparer_rejects_resolution_below_minimum() -> None:
    raw_small = make_test_photo(200, 200)
    preparer = PersonPhotoPreparer()

    with pytest.raises(PhotoPreparationError) as exc_info:
        preparer.prepare(raw_small)
    assert exc_info.value.code == "resolution_too_low"


def test_preparer_rejects_corrupted_payload() -> None:
    preparer = PersonPhotoPreparer()
    with pytest.raises(PhotoPreparationError) as exc_info:
        preparer.prepare(b"not_an_image_binary_data")
    assert exc_info.value.code in ("corrupted_image", "decode_failed")


def test_preparer_detects_framing_and_aspect_ratio() -> None:
    preparer = PersonPhotoPreparer(detector=MockPersonDetector(person_count=1))

    # Portrait framing (0.75)
    portrait_bytes = make_test_photo(600, 800)
    portrait_res = preparer.prepare(portrait_bytes)
    assert "landscape_orientation" not in portrait_res.quality_reasons
    assert portrait_res.framing_score >= 0.8
    assert portrait_res.ready_for_tryon is True

    # Landscape framing (1.5)
    landscape_bytes = make_test_photo(900, 600)
    landscape_res = preparer.prepare(landscape_bytes)
    assert "landscape_orientation" in landscape_res.quality_reasons
    assert landscape_res.ready_for_tryon is False


def test_preparer_exposure_and_contrast_heuristics() -> None:
    preparer = PersonPhotoPreparer(detector=MockPersonDetector(person_count=1))

    # Underexposed
    dark_bytes = make_test_photo(600, 800, color=(15, 15, 15), add_gradient=False)
    dark_res = preparer.prepare(dark_bytes)
    assert "underexposed" in dark_res.quality_reasons
    assert dark_res.ready_for_tryon is False

    # Overexposed
    bright_bytes = make_test_photo(600, 800, color=(245, 245, 245), add_gradient=False)
    bright_res = preparer.prepare(bright_bytes)
    assert "overexposed" in bright_res.quality_reasons
    assert bright_res.ready_for_tryon is False

    # Low contrast
    flat_bytes = make_test_photo(600, 800, color=(128, 128, 128), add_gradient=False)
    flat_res = preparer.prepare(flat_bytes)
    assert "low_contrast" in flat_res.quality_reasons


def test_detector_person_count_and_tryon_readiness() -> None:
    photo_bytes = make_test_photo(600, 800)

    # 1 person detected -> ready
    prep_single = PersonPhotoPreparer(detector=MockPersonDetector(person_count=1))
    res_single = prep_single.prepare(photo_bytes)
    assert res_single.has_person is True
    assert res_single.ready_for_tryon is True

    # 0 persons detected -> not ready
    prep_none = PersonPhotoPreparer(detector=MockPersonDetector(person_count=0))
    res_none = prep_none.prepare(photo_bytes)
    assert res_none.has_person is False
    assert "no_person_detected" in res_none.quality_reasons
    assert res_none.ready_for_tryon is False

    # >1 persons detected -> not ready
    prep_multi = PersonPhotoPreparer(detector=MockPersonDetector(person_count=3))
    res_multi = prep_multi.prepare(photo_bytes)
    assert res_multi.has_person is False
    assert "multiple_people_detected" in res_multi.quality_reasons
    assert res_multi.ready_for_tryon is False


@pytest.mark.asyncio
async def test_user_photo_upload_service_success_persists_full_metadata(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    # Create user with consent
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)]
        )
    )

    photo_bytes = make_test_photo(600, 800, color=(160, 130, 95))
    service = UserPhotoUploadService(
        uow=uow,
        storage=storage,
        preparer=PersonPhotoPreparer(detector=MockPersonDetector(person_count=1, provider="unit_test")),
    )

    cmd = PrepareUserPhotoCommand(
        user_id=profile.user_id,
        photo_bytes=photo_bytes,
        photo_type=PhotoType.TRYON_REFERENCE,
    )
    result = await service.execute(cmd)

    assert result.status == PhotoStatus.ACCEPTED.value
    assert result.ready_for_tryon is True
    assert result.storage_key is not None
    assert result.content_sha256 is not None
    assert result.width == 600
    assert result.height == 800
    assert result.has_person is True
    assert result.has_face is True
    assert result.quality_score is not None and result.quality_score > 0.5
    assert result.skin_tone is not None
    assert await storage.exists(result.storage_key)

    # Verify persisted DB row
    async with uow:
        db_photo = await uow.photos.get_by_id(result.photo_id)
        assert db_photo is not None
        assert db_photo.content_sha256 == result.content_sha256
        assert db_photo.width == 600
        assert db_photo.height == 800
        assert db_photo.image_format == "JPEG"
        assert db_photo.has_person is True
        assert db_photo.ready_for_tryon is True
        assert db_photo.pose_provider == "unit_test"


@pytest.mark.asyncio
async def test_user_photo_upload_service_rejects_without_consent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(CreateProfileCommand())

    photo_bytes = make_test_photo(600, 800)
    service = UserPhotoUploadService(uow=uow, storage=storage)

    cmd = PrepareUserPhotoCommand(user_id=profile.user_id, photo_bytes=photo_bytes)
    with pytest.raises(ConsentRequiredError) as exc_info:
        await service.execute(cmd)
    assert exc_info.value.data_type == DataType.BODY_PHOTO.value


@pytest.mark.asyncio
async def test_user_photo_upload_service_rejects_under_18(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(CreateProfileCommand())

    # User records is_18_or_older=False (granted must be False per DB constraint)
    async with uow:
        await uow.consents.upsert(
            user_id=profile.user_id,
            data_type=DataType.BODY_PHOTO.value,
            granted=False,
            is_18_or_older=False,
        )
        await uow.commit()

    photo_bytes = make_test_photo(600, 800)
    service = UserPhotoUploadService(uow=uow, storage=storage)

    cmd = PrepareUserPhotoCommand(user_id=profile.user_id, photo_bytes=photo_bytes)
    with pytest.raises(ConsentRequiredError) as exc_info:
        await service.execute(cmd)
    assert "18 or older" in str(exc_info.value)


@pytest.mark.asyncio
async def test_user_photo_upload_service_rejects_consent_version_mismatch(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)]
        )
    )

    photo_bytes = make_test_photo(600, 800)
    service = UserPhotoUploadService(uow=uow, storage=storage)

    cmd = PrepareUserPhotoCommand(
        user_id=profile.user_id,
        photo_bytes=photo_bytes,
        expected_consent_version="9999.1",
    )
    with pytest.raises(ConsentRequiredError) as exc_info:
        await service.execute(cmd)
    assert "Consent version mismatch" in str(exc_info.value)


@pytest.mark.asyncio
async def test_user_photo_upload_service_storage_cleanup_on_db_failure(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    storage = InMemoryStorageAdapter()

    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(
            consents=[ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=True)]
        )
    )

    photo_bytes = make_test_photo(600, 800)
    service = UserPhotoUploadService(uow=uow, storage=storage)

    from fashx.profile.repositories.profile_repository import UserPhotoRepository

    async def failing_create(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Database connection lost during insert")

    monkeypatch.setattr(UserPhotoRepository, "create", failing_create)

    cmd = PrepareUserPhotoCommand(
        user_id=profile.user_id,
        photo_bytes=photo_bytes,
    )
    with pytest.raises(RuntimeError, match="Database connection lost"):
        await service.execute(cmd)

    # Verify that storage was purged as compensating rollback
    assert len(storage._objects) == 0
