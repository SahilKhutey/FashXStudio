from __future__ import annotations

from asyncio import to_thread

from datetime import datetime
from uuid import UUID, uuid4

from api.app.core.errors import AuthorizationError, ConsentRequiredError, NotFoundError
from api.app.core.settings import get_settings
from api.app.core.transactions import transaction
from api.app.ports.queue import QueuePort
from api.app.ports.storage import ObjectStoragePort
from api.app.profile.repositories.media import ProfileMediaRepository
from schemas.common.enums import DataType, PhotoType


class ProfileMediaApplicationService:
    def __init__(
        self,
        repository: ProfileMediaRepository,
        storage: ObjectStoragePort,
        queue: QueuePort,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.queue = queue

    async def set_consent(self, user_id: UUID, *, data_type: DataType, granted: bool):
        async with transaction(self.repository.session):
            return await self.repository.upsert_consent(user_id, data_type.value, granted)

    async def require_consent(self, user_id: UUID, data_type: DataType) -> None:
        record = await self.repository.get_consent(user_id, data_type.value)
        if record is None or not record.granted:
            raise ConsentRequiredError(data_type.value)

    async def create_photo_upload(
        self,
        user_id: UUID,
        *,
        photo_type: PhotoType,
        content_type: str,
        file_size_bytes: int,
    ):
        await self.require_consent(user_id, DataType.BODY_PHOTO)
        key = f"user-photos/{user_id}/{uuid4()}.{content_type.split('/', 1)[1]}"
        async with transaction(self.repository.session):
            photo = await self.repository.create_photo(
                user_id=user_id,
                photo_type=photo_type.value,
                storage_key=key,
            )
            upload_url, expires_at = await to_thread(self.storage.create_upload_url,
                key=key,
                content_type=content_type,
                expires_in=get_settings().r2_upload_url_ttl_seconds,
            )
            return photo, upload_url, expires_at

    async def complete_photo_upload(self, user_id: UUID, photo_id: UUID):
        await self.require_consent(user_id, DataType.BODY_PHOTO)
        async with transaction(self.repository.session):
            photo = await self.repository.get_photo(user_id, photo_id)
            if photo is None:
                raise NotFoundError("Photo not found")
            if photo.status not in {"upload_pending", "processing"}:
                raise AuthorizationError("Photo is not eligible for processing")
            if photo.status == "processing":
                existing = await self.repository.get_latest_photo_job(user_id, photo_id)
                if existing:
                    return photo, existing
            await to_thread(self.storage.head_object, key=photo.storage_key)
            job = await self.repository.set_photo_processing(photo)
            await self.queue.enqueue(
                queue="profile-photo-processing",
                payload={"job_id": str(job.id), "photo_id": str(photo.id), "user_id": str(user_id)},
            )
            return photo, job

    async def get_photo_status(self, user_id: UUID, photo_id: UUID):
        async with transaction(self.repository.session):
            photo = await self.repository.get_photo(user_id, photo_id)
            if photo is None:
                raise NotFoundError("Photo not found")
            return photo


    async def get_capture_guidance(self, user_id: UUID, photo_id: UUID) -> dict:
        async with transaction(self.repository.session):
            photo = await self.repository.get_photo(user_id, photo_id)
            if photo is None:
                raise NotFoundError("Photo not found")
            from api.app.profile.domain.capture_guidance import build_capture_guidance
            return build_capture_guidance(
                photo_id=photo.id,
                status=photo.status,
                ready_for_tryon=photo.ready_for_tryon,
                quality_score=photo.quality_score,
                reasons=photo.quality_reasons or [],
            )

    async def create_scoped_media_url(
        self,
        *,
        photo_id: UUID,
        purpose: str,
        job_id: UUID,
    ) -> tuple[str, datetime]:
        if purpose not in {"tryon", "skin_tone"}:
            raise AuthorizationError("Unsupported media access purpose")
        async with transaction(self.repository.session):
            job = await self.repository.get_photo_job(job_id)
            if job is None or job.photo_id != photo_id:
                raise AuthorizationError("Invalid media access scope")
            await self.require_consent(job.user_id, DataType.BODY_PHOTO)
            photo = await self.repository.get_photo(job.user_id, photo_id)
            if photo is None or photo.user_id != job.user_id:
                raise NotFoundError("Photo not found")
            if photo.status != "accepted":
                raise AuthorizationError("Photo is not available for scoped access")
            return await to_thread(self.storage.create_download_url,
                key=photo.storage_key,
                expires_in=get_settings().r2_download_url_ttl_seconds,
            )
