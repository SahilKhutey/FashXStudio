from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import ProfilePhotoJob, UserPhoto
from api.app.core.settings import get_settings


class ProfilePhotoJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def claim(self, job_id: UUID) -> tuple[ProfilePhotoJob | None, UserPhoto | None, bool]:
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=get_settings().profile_photo_lock_timeout_seconds)
        from sqlalchemy import or_, and_
        eligibility = or_(
            ProfilePhotoJob.status == "queued",
            and_(ProfilePhotoJob.status == "processing", ProfilePhotoJob.locked_at.is_not(None), ProfilePhotoJob.locked_at < stale_before),
        )
        result = await self.session.execute(
            update(ProfilePhotoJob)
            .where(
                ProfilePhotoJob.id == job_id,
                eligibility,
            )
            .values(
                status="processing",
                attempt_count=ProfilePhotoJob.attempt_count + 1,
                locked_at=now,
            )
            .returning(ProfilePhotoJob.id)
        )
        claimed_id = result.scalar_one_or_none()
        if claimed_id is None:
            return None, None, False
        job = await self.session.get(ProfilePhotoJob, claimed_id)
        photo = await self.session.get(UserPhoto, job.photo_id) if job else None
        return job, photo, bool(job and photo)

    async def complete(self, job_id: UUID, *, result: dict) -> ProfilePhotoJob:
        job = await self.session.get(ProfilePhotoJob, job_id)
        if job is None:
            raise LookupError("Photo processing job not found")
        photo = await self.session.get(UserPhoto, job.photo_id)
        if photo is None:
            raise LookupError("Profile photo not found")
        photo.status = "accepted"
        photo.reject_reason = None
        photo.content_sha256 = result["content_sha256"]
        photo.width = result["width"]
        photo.height = result["height"]
        photo.image_format = result["image_format"]
        photo.has_person = result.get("has_person")
        photo.has_face = result.get("has_face")
        photo.file_size_bytes = result.get("file_size_bytes")
        photo.quality_score = result.get("quality_score")
        photo.pose_score = result.get("pose_score")
        photo.framing_score = result.get("framing_score")
        photo.landmark_confidence = result.get("landmark_confidence")
        photo.ready_for_tryon = result.get("ready_for_tryon")
        photo.quality_reasons = result.get("quality_reasons") or []
        photo.pose_provider = result.get("pose_provider")
        photo.pose_provider_version = result.get("pose_provider_version")
        job.status = "completed"
        job.failure_reason = None
        job.last_error = None
        job.locked_at = None
        job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return job

    async def fail(
        self,
        job_id: UUID,
        *,
        reason: str,
        retryable: bool,
        max_attempts: int,
    ) -> tuple[ProfilePhotoJob, bool]:
        job = await self.session.get(ProfilePhotoJob, job_id)
        if job is None:
            raise LookupError("Photo processing job not found")
        photo = await self.session.get(UserPhoto, job.photo_id)
        if photo is None:
            raise LookupError("Profile photo not found")

        should_retry = retryable and job.attempt_count < max_attempts
        job.failure_reason = reason
        job.last_error = reason
        job.locked_at = None
        if should_retry:
            job.status = "queued"
            photo.status = "processing"
        else:
            job.status = "failed"
            photo.status = "rejected"
            photo.reject_reason = reason
            job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return job, should_retry
