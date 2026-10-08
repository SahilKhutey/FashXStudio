from dataclasses import dataclass
from uuid import UUID

from api.app.core.errors import EntityNotFoundError
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork


@dataclass(frozen=True)
class GetJobStatusResult:
    job_id: UUID
    status: str
    artifact_key: str
    result_url: str | None
    failure_reason: str | None
    model_version: str
    pipeline_version: str


class GetTryOnJobStatusUseCase:
    """Retrieves asynchronous try-on job status, progress, and artifact link."""

    def __init__(self, tryon_uow: TryOnUnitOfWork) -> None:
        self.tryon_uow = tryon_uow

    async def execute(self, job_id: UUID) -> GetJobStatusResult:
        async with self.tryon_uow:
            job = await self.tryon_uow.jobs.get_by_id(job_id)
            if job is None:
                raise EntityNotFoundError("TryOnJob", job_id)

            result_url: str | None = None
            if job.status == "completed":
                artifact = await self.tryon_uow.artifacts.get_by_job_id(job.id)
                if artifact:
                    result_url = artifact.result_key

            return GetJobStatusResult(
                job_id=job.id,
                status=job.status,
                artifact_key=job.artifact_key,
                result_url=result_url,
                failure_reason=job.failure_reason,
                model_version=job.model_version,
                pipeline_version=job.pipeline_version,
            )
