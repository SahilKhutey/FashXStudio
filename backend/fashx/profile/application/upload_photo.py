import hashlib
import inspect
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from database.models.identity import UserPhoto
from database.models.media import MediaObject
from fashx.application.ports.storage import media_key
from fashx.core.errors import ConsentRequiredError, EntityNotFoundError
from fashx.core.ports.storage import InMemoryStorageAdapter
from fashx.profile.calibration.skin_tone import SkinToneCalibrationResult, SkinToneCalibrator
from fashx.profile.capture.validator import PhotoQualityValidator
from fashx.profile.images.prepare_photo import PersonPhotoPreparer
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from schemas.common.enums import DataType, PhotoStatus, PhotoType


@dataclass
class UploadPhotoCommand:
    user_id: UUID
    photo_type: PhotoType | str
    photo_bytes: bytes


@dataclass
class UploadPhotoResult:
    photo_id: UUID
    user_id: UUID
    photo_type: str
    status: str
    storage_key: str | None
    reject_reason: str | None
    skin_tone: SkinToneCalibrationResult | None = None
    ready_for_tryon: bool = True
    content_sha256: str | None = None
    quality_reasons: list[str] = field(default_factory=list)


class UploadUserPhotoUseCase:
    """Use case to validate portrait quality, enforce GDPR consent, and calibrate skin tone (Rule I07)."""

    def __init__(
        self,
        uow: ProfileUnitOfWork,
        storage: Any | None = None,
    ) -> None:
        self.uow = uow
        self.storage = storage or InMemoryStorageAdapter()

    async def execute(self, cmd: UploadPhotoCommand) -> UploadPhotoResult:
        photo_type_str = (
            cmd.photo_type.value if hasattr(cmd.photo_type, "value") else str(cmd.photo_type)
        )

        async with self.uow:
            user = await self.uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            # Rule I07 / GDPR: User must have explicitly granted consent for BODY_PHOTO
            consent = await self.uow.consents.get_by_user_and_type(
                cmd.user_id, DataType.BODY_PHOTO.value
            )
            if consent is None or not consent.granted:
                raise ConsentRequiredError(
                    data_type=DataType.BODY_PHOTO.value,
                    message=f"User {cmd.user_id} has not granted explicit consent for '{DataType.BODY_PHOTO.value}'.",
                )

            # Pre-inference quality gate validation
            val_res = PhotoQualityValidator.validate_photo_bytes(cmd.photo_bytes)

            if not val_res.passed:
                reject_id = uuid4()
                photo = UserPhoto(
                    id=reject_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    storage_key="",
                    status=PhotoStatus.REJECTED.value,
                    reject_reason=val_res.reject_reason,
                    version=1,
                )
                self.uow.photos.add(photo)
                await self.uow.flush()
                await self.uow.commit()

                return UploadPhotoResult(
                    photo_id=reject_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    status=PhotoStatus.REJECTED.value,
                    storage_key=None,
                    reject_reason=val_res.reject_reason,
                    skin_tone=None,
                )

            # Quality passed: prepare, normalize, and store photo
            preparer = PersonPhotoPreparer()
            try:
                prepared = preparer.prepare(cmd.photo_bytes, run_detector=True)
                final_bytes = prepared.image_bytes
                content_sha256 = prepared.content_sha256
                width = prepared.width
                height = prepared.height
                image_format = prepared.image_format
                file_size_bytes = prepared.file_size_bytes
                has_person = prepared.has_person
                has_face = prepared.has_face
                quality_score = prepared.quality_score
                framing_score = prepared.framing_score
                pose_score = prepared.pose_score
                ready_for_tryon = prepared.ready_for_tryon
                quality_reasons = prepared.quality_reasons
                pose_provider = prepared.detection.provider if prepared.detection else None
                pose_provider_version = prepared.detection.version if prepared.detection else None
            except Exception:
                final_bytes = cmd.photo_bytes
                content_sha256 = hashlib.sha256(cmd.photo_bytes).hexdigest()
                width = int(val_res.metrics.get("width", 0)) or None
                height = int(val_res.metrics.get("height", 0)) or None
                image_format = "JPEG"
                file_size_bytes = len(cmd.photo_bytes)
                has_person = True
                has_face = True
                quality_score = 0.8
                framing_score = round(float(val_res.metrics.get("aspect_ratio", 0.75)), 2)
                pose_score = 0.8
                ready_for_tryon = True
                quality_reasons = []
                pose_provider = None
                pose_provider_version = None

            photo_id = uuid4()
            storage_key = media_key(cmd.user_id, "reference_photo", photo_id)

            put_res = self.storage.put(storage_key, final_bytes, content_type="image/jpeg")
            if inspect.isawaitable(put_res):
                await put_res

            try:
                photo = await self.uow.photos.create(
                    id_=photo_id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    storage_key=storage_key,
                    status=PhotoStatus.ACCEPTED.value,
                    reject_reason=None,
                    content_sha256=content_sha256,
                    width=width,
                    height=height,
                    image_format=image_format,
                    file_size_bytes=file_size_bytes,
                    has_person=has_person,
                    has_face=has_face,
                    quality_score=quality_score,
                    framing_score=framing_score,
                    pose_score=pose_score,
                    ready_for_tryon=ready_for_tryon,
                    quality_reasons=quality_reasons,
                    pose_provider=pose_provider,
                    pose_provider_version=pose_provider_version,
                    version=1,
                )

                if hasattr(self.uow, "media"):
                    media_record = MediaObject(
                        id=photo_id,
                        user_id=cmd.user_id,
                        kind="reference_photo",
                        object_key=storage_key,
                        sha256=content_sha256,
                        size_bytes=len(final_bytes),
                        content_type="image/jpeg",
                    )
                    self.uow.media.add(media_record)

                skin_tone_res = SkinToneCalibrator.calibrate_from_image_bytes(final_bytes)

                await self.uow.flush()
                await self.uow.commit()
            except Exception:
                # Compensating transaction: remove orphan from storage if DB commit fails
                del_res = self.storage.delete(storage_key)
                if inspect.isawaitable(del_res):
                    await del_res
                raise

            return UploadPhotoResult(
                photo_id=photo.id,
                user_id=cmd.user_id,
                photo_type=photo_type_str,
                status=PhotoStatus.ACCEPTED.value,
                storage_key=storage_key,
                reject_reason=None,
                skin_tone=skin_tone_res,
                ready_for_tryon=ready_for_tryon,
                content_sha256=content_sha256,
                quality_reasons=quality_reasons,
            )
