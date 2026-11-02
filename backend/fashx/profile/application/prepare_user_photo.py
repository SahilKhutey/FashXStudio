from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from database.models.media import MediaObject
from fashx.application.ports.storage import media_key
from fashx.core.errors import ConsentRequiredError, EntityNotFoundError
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.core.settings import get_settings
from fashx.profile.calibration.skin_tone import SkinToneCalibrationResult, SkinToneCalibrator
from fashx.profile.images.prepare_photo import (
    PersonPhotoPreparer,
    PhotoPreparationError,
    PreparedPhoto,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from schemas.common.enums import DataType, PhotoStatus, PhotoType


@dataclass
class PrepareUserPhotoCommand:
    user_id: UUID
    photo_bytes: bytes
    photo_type: PhotoType | str = PhotoType.TRYON_REFERENCE
    run_detector: bool = True
    enforce_consent: bool = True
    expected_consent_version: str | None = None


@dataclass
class PrepareUserPhotoResult:
    photo_id: UUID
    user_id: UUID
    photo_type: str
    status: str
    storage_key: str | None
    ready_for_tryon: bool
    content_sha256: str | None
    width: int | None
    height: int | None
    quality_score: float | None
    framing_score: float | None
    pose_score: float | None
    has_person: bool | None
    has_face: bool | None
    quality_reasons: list[str] = field(default_factory=list)
    reject_reason: str | None = None
    skin_tone: SkinToneCalibrationResult | None = None


class UserPhotoUploadService:
    """Prepares, validates, and securely stores user portrait photos for virtual try-on."""

    def __init__(
        self,
        uow: ProfileUnitOfWork,
        storage: Any | None = None,
        preparer: PersonPhotoPreparer | None = None,
        consent_version: str | None = None,
    ) -> None:
        self.uow = uow
        self.storage = storage or InMemoryStorageAdapter()
        self.preparer = preparer or PersonPhotoPreparer()
        self.consent_version = consent_version or get_settings().consent_version

    async def execute(self, cmd: PrepareUserPhotoCommand) -> PrepareUserPhotoResult:
        photo_type_str = (
            cmd.photo_type.value if hasattr(cmd.photo_type, "value") else str(cmd.photo_type)
        )

        async with self.uow:
            user = await self.uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            # 1. Enforce explicit consent and adult verification
            if cmd.enforce_consent:
                consent = await self.uow.consents.get_by_user_and_type(
                    cmd.user_id, DataType.BODY_PHOTO.value
                )
                if consent is not None and consent.is_18_or_older is False:
                    raise ConsentRequiredError(
                        data_type=DataType.BODY_PHOTO.value,
                        message=f"User {cmd.user_id} is not verified as 18 or older.",
                    )
                if consent is None or not consent.granted:
                    raise ConsentRequiredError(
                        data_type=DataType.BODY_PHOTO.value,
                        message=f"User {cmd.user_id} has not granted explicit consent for '{DataType.BODY_PHOTO.value}'.",
                    )
                target_version = cmd.expected_consent_version or self.consent_version
                if target_version and consent.consent_version != target_version:
                    raise ConsentRequiredError(
                        data_type=DataType.BODY_PHOTO.value,
                        message=(
                            f"Consent version mismatch: record is '{consent.consent_version}', "
                            f"required is '{target_version}'."
                        ),
                    )

            # 2. Prepare photo (validation, EXIF normalization, cropping, lighting, person detection)
            try:
                prepared: PreparedPhoto = self.preparer.prepare(
                    cmd.photo_bytes,
                    run_detector=cmd.run_detector,
                )
            except PhotoPreparationError as ppe:
                reject_id = uuid4()
                await self.uow.photos.create(
                    id_=reject_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    storage_key="",
                    status=PhotoStatus.REJECTED.value,
                    reject_reason=ppe.message,
                    ready_for_tryon=False,
                    quality_reasons=[ppe.code],
                )
                await self.uow.commit()

                return PrepareUserPhotoResult(
                    photo_id=reject_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    status=PhotoStatus.REJECTED.value,
                    storage_key=None,
                    ready_for_tryon=False,
                    content_sha256=None,
                    width=None,
                    height=None,
                    quality_score=0.0,
                    framing_score=0.0,
                    pose_score=0.0,
                    has_person=False,
                    has_face=False,
                    quality_reasons=[ppe.code],
                    reject_reason=ppe.message,
                    skin_tone=None,
                )

            # 3. Upload prepared JPEG to storage
            photo_id = uuid4()
            storage_key = media_key(cmd.user_id, "reference_photo", photo_id)

            put_res = self.storage.put(storage_key, prepared.image_bytes, content_type="image/jpeg")
            if inspect.isawaitable(put_res):
                await put_res

            # 4. Persist photo record and media object with compensating transaction
            try:
                await self.uow.photos.create(
                    id_=photo_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    storage_key=storage_key,
                    status=PhotoStatus.ACCEPTED.value,
                    content_sha256=prepared.content_sha256,
                    width=prepared.width,
                    height=prepared.height,
                    image_format=prepared.image_format,
                    file_size_bytes=prepared.file_size_bytes,
                    has_person=prepared.has_person,
                    has_face=prepared.has_face,
                    quality_score=prepared.quality_score,
                    pose_score=prepared.pose_score,
                    framing_score=prepared.framing_score,
                    ready_for_tryon=prepared.ready_for_tryon,
                    quality_reasons=prepared.quality_reasons,
                    pose_provider=prepared.detection.provider if prepared.detection else None,
                    pose_provider_version=prepared.detection.version if prepared.detection else None,
                )

                if hasattr(self.uow, "media"):
                    media_record = MediaObject(
                        id=photo_id,
                        user_id=cmd.user_id,
                        kind="reference_photo",
                        object_key=storage_key,
                        sha256=prepared.content_sha256,
                        size_bytes=prepared.file_size_bytes,
                        content_type="image/jpeg",
                    )
                    self.uow.media.add(media_record)

                skin_tone_res = SkinToneCalibrator.calibrate_from_image_bytes(prepared.image_bytes)

                await self.uow.flush()
                await self.uow.commit()
            except Exception:
                del_res = self.storage.delete(storage_key)
                if inspect.isawaitable(del_res):
                    await del_res
                raise

            return PrepareUserPhotoResult(
                photo_id=photo_id,
                user_id=cmd.user_id,
                photo_type=photo_type_str,
                status=PhotoStatus.ACCEPTED.value,
                storage_key=storage_key,
                ready_for_tryon=prepared.ready_for_tryon,
                content_sha256=prepared.content_sha256,
                width=prepared.width,
                height=prepared.height,
                quality_score=prepared.quality_score,
                framing_score=prepared.framing_score,
                pose_score=prepared.pose_score,
                has_person=prepared.has_person,
                has_face=prepared.has_face,
                quality_reasons=prepared.quality_reasons,
                reject_reason=None,
                skin_tone=skin_tone_res,
            )


# Alias for compatibility with use case naming convention
PrepareUserPhotoUseCase = UserPhotoUploadService
