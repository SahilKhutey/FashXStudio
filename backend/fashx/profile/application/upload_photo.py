from dataclasses import dataclass
from uuid import UUID, uuid4

from database.models.identity import UserPhoto
from schemas.common.enums import DataType, PhotoStatus, PhotoType

from api.app.core.errors import ConsentRequiredError, EntityNotFoundError
from api.app.core.ports.storage import InMemoryStorageAdapter, StoragePort
from fashx.profile.calibration.skin_tone import SkinToneCalibrationResult, SkinToneCalibrator
from fashx.profile.capture.validator import PhotoQualityValidator
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


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


class UploadUserPhotoUseCase:
    """Use case to validate portrait quality, enforce GDPR consent, and calibrate skin tone (Rule I07)."""

    def __init__(
        self,
        uow: ProfileUnitOfWork,
        storage: StoragePort | None = None,
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
                photo = UserPhoto(
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
                    photo_id=photo.id,
                    user_id=cmd.user_id,
                    photo_type=photo_type_str,
                    status=PhotoStatus.REJECTED.value,
                    storage_key=None,
                    reject_reason=val_res.reject_reason,
                    skin_tone=None,
                )

            # Quality passed: store photo and calibrate skin tone
            storage_key = f"users/{cmd.user_id}/photos/{uuid4()}.png"
            await self.storage.put(storage_key, cmd.photo_bytes, content_type="image/png")

            photo = UserPhoto(
                user_id=cmd.user_id,
                photo_type=photo_type_str,
                storage_key=storage_key,
                status=PhotoStatus.ACCEPTED.value,
                reject_reason=None,
                version=1,
            )
            self.uow.photos.add(photo)

            skin_tone_res = SkinToneCalibrator.calibrate_from_image_bytes(cmd.photo_bytes)

            await self.uow.flush()
            await self.uow.commit()

            return UploadPhotoResult(
                photo_id=photo.id,
                user_id=cmd.user_id,
                photo_type=photo_type_str,
                status=PhotoStatus.ACCEPTED.value,
                storage_key=storage_key,
                reject_reason=None,
                skin_tone=skin_tone_res,
            )
