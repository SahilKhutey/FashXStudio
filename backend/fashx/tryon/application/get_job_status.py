from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.errors import EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


@dataclass(frozen=True)
class GetJobStatusResult:
    job_id: UUID
    garment_id: UUID
    status: str
    artifact_key: str
    result_url: str | None
    failure_reason: str | None
    model_version: str
    pipeline_version: str
    provider: str | None = None
    reference_photo_key: str | None = None


class GetTryOnJobStatusUseCase:
    """Retrieves asynchronous try-on job status, progress, and artifact link."""

    def __init__(
        self,
        tryon_uow: TryOnUnitOfWork,
        profile_uow: ProfileUnitOfWork | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow

    async def execute(self, job_id: UUID, user_id: str | None = None) -> GetJobStatusResult:
        async with self.tryon_uow:
            job = await self.tryon_uow.jobs.get_by_id(job_id)
            if job is None or (user_id is not None and str(job.user_id) != str(user_id)):
                raise EntityNotFoundError("TryOnJob", job_id)

            result_url: str | None = None
            if job.status == "completed":
                artifact = await self.tryon_uow.artifacts.get_by_job_id(job.id)
                if artifact:
                    result_url = artifact.result_key

            job_id_val = job.id
            garment_id_val = job.garment_id
            status_val = job.status
            artifact_key_val = job.artifact_key
            failure_reason_val = job.failure_reason
            model_version_val = job.model_version
            pipeline_version_val = job.pipeline_version
            provider_val = getattr(job, "provider", None)
            profile_photo_id_val = job.profile_photo_id
            user_id_val = job.user_id

        reference_photo_key: str | None = None
        if profile_photo_id_val and self.profile_uow:
            async with self.profile_uow:
                has_consent = await self.profile_uow.consents.has_consent(user_id_val, "body_photo")
                if has_consent:
                    photo = await self.profile_uow.photos.get_by_id(profile_photo_id_val)
                    if photo and photo.status == "accepted" and photo.storage_key:
                        reference_photo_key = photo.storage_key

        return GetJobStatusResult(
            job_id=job_id_val,
            garment_id=garment_id_val,
            status=status_val,
            artifact_key=artifact_key_val,
            result_url=result_url,
            failure_reason=failure_reason_val,
            model_version=model_version_val,
            pipeline_version=pipeline_version_val,
            provider=provider_val,
            reference_photo_key=reference_photo_key,
        )
