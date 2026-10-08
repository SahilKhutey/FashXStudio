from __future__ import annotations

from uuid import UUID

from api.app.core.settings import get_settings
from api.app.core.transactions import transaction
from api.app.profile.repositories.media_jobs import ProfilePhotoJobRepository
from database.models.identity import UserPhoto
from api.app.ports.queue import QueuePort


class ProfilePhotoJobApplicationService:
    def __init__(self, repository: ProfilePhotoJobRepository, queue: QueuePort) -> None:
        self.repository = repository
        self.queue = queue

    async def claim(self, job_id: UUID) -> dict:
        async with transaction(self.repository.session):
            job, photo, claimed = await self.repository.claim(job_id)
            if not claimed or job is None or photo is None:
                return {"claimed": False, "reason": "already_claimed_or_terminal"}
            return {
                "claimed": True,
                "job_id": job.id,
                "photo_id": photo.id,
                "user_id": photo.user_id,
                "photo_type": photo.photo_type,
                "storage_key": photo.storage_key,
                "attempt_count": job.attempt_count,
            }

    async def complete(self, job_id: UUID, result: dict) -> dict:
        async with transaction(self.repository.session):
            job = await self.repository.complete(job_id, result=result)
            photo = await self.repository.session.get(UserPhoto, job.photo_id)
            user_id = job.user_id
            photo_type = photo.photo_type if photo else None
            payload = {"status": job.status, "job_id": str(job.id), "photo_id": str(job.photo_id), "user_id": str(user_id), "photo_type": photo_type}
        if photo_type == "skin_tone":
            await self.queue.enqueue(queue="skin-tone-processing", payload=payload)
        return {"status": job.status, "job_id": job.id, "photo_id": job.photo_id}

    async def fail(self, job_id: UUID, *, reason: str, retryable: bool) -> dict:
        async with transaction(self.repository.session):
            job, should_retry = await self.repository.fail(
                job_id,
                reason=reason,
                retryable=retryable,
                max_attempts=get_settings().profile_photo_max_attempts,
            )
            result = {
                "status": job.status,
                "retry_scheduled": should_retry,
                "attempt_count": job.attempt_count,
                "failure_reason": job.failure_reason,
                "job_id": str(job.id),
                "photo_id": str(job.photo_id),
                "user_id": str(job.user_id),
            }

        if should_retry:
            await self.queue.enqueue(
                queue="profile-photo-processing",
                payload={
                    "job_id": result["job_id"],
                    "photo_id": result["photo_id"],
                    "user_id": result["user_id"],
                },
            )
        elif result["status"] == "failed":
            await self.queue.enqueue(
                queue="profile-photo-processing-dlq",
                payload={
                    "job_id": result["job_id"],
                    "photo_id": result["photo_id"],
                    "user_id": result["user_id"],
                    "reason": reason,
                },
            )
        return {k: result[k] for k in ("status", "retry_scheduled", "attempt_count", "failure_reason")}
