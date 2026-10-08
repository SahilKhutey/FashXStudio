import uuid

from api.app.tryon.repositories.tryon_repository import TryOnRepository
from app.repositories.models import TryOnJobModel


class GetTryOnStatusUseCase:
    def __init__(self, repo: TryOnRepository):
        self.repo = repo

    async def execute(self, job_id: uuid.UUID) -> TryOnJobModel | None:
        return await self.repo.get_by_id(job_id)


class CancelTryOnUseCase:
    def __init__(self, repo: TryOnRepository):
        self.repo = repo

    async def execute(self, job_id: uuid.UUID) -> TryOnJobModel | None:
        return await self.repo.cancel_job(job_id)
