from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import ConsentRecord, ProfilePhotoJob, UserPhoto


class ProfileMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_consent(self, user_id: UUID, data_type: str) -> ConsentRecord | None:
        stmt = select(ConsentRecord).where(
            ConsentRecord.user_id == user_id,
            ConsentRecord.data_type == data_type,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert_consent(self, user_id: UUID, data_type: str, granted: bool) -> ConsentRecord:
        current = await self.get_consent(user_id, data_type)
        if current is None:
            current = ConsentRecord(user_id=user_id, data_type=data_type, granted=granted)
            self.session.add(current)
        else:
            current.granted = granted
        await self.session.flush()
        return current

    async def create_photo(self, *, user_id: UUID, photo_type: str, storage_key: str) -> UserPhoto:
        photo = UserPhoto(
            user_id=user_id,
            photo_type=photo_type,
            storage_key=storage_key,
            status="upload_pending",
            version=1,
        )
        self.session.add(photo)
        await self.session.flush()
        return photo

    async def get_photo(self, user_id: UUID, photo_id: UUID) -> UserPhoto | None:
        stmt = select(UserPhoto).where(UserPhoto.user_id == user_id, UserPhoto.id == photo_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_latest_photo_job(self, user_id: UUID, photo_id: UUID) -> ProfilePhotoJob | None:
        stmt = select(ProfilePhotoJob).where(
            ProfilePhotoJob.user_id == user_id,
            ProfilePhotoJob.photo_id == photo_id,
        ).order_by(ProfilePhotoJob.created_at.desc())
        return (await self.session.execute(stmt)).scalars().first()

    async def get_photo_job(self, job_id: UUID) -> ProfilePhotoJob | None:
        return await self.session.get(ProfilePhotoJob, job_id)


    async def update_validation(self, photo: UserPhoto, *, result: dict) -> UserPhoto:
        for field in (
            "content_sha256", "width", "height", "image_format", "file_size_bytes",
            "has_person", "has_face", "quality_score", "pose_score", "framing_score",
            "landmark_confidence", "ready_for_tryon", "quality_reasons",
            "pose_provider", "pose_provider_version",
        ):
            if field in result:
                setattr(photo, field, result[field])
        await self.session.flush()
        return photo

    async def set_photo_processing(self, photo: UserPhoto) -> ProfilePhotoJob:
        photo.status = "processing"
        job = ProfilePhotoJob(photo_id=photo.id, user_id=photo.user_id, status="queued")
        self.session.add(job)
        await self.session.flush()
        return job
