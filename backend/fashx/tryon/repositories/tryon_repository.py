from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from uuid import UUID

from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork
from database.models.tryon import TryOnArtifact, TryOnJob
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class TryOnJobRepository(BaseRepository[TryOnJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnJob)

    async def get_by_user_and_idempotency(
        self, user_id: UUID, idempotency_key: str
    ) -> TryOnJob | None:
        stmt = select(TryOnJob).where(
            TryOnJob.user_id == user_id,
            TryOnJob.idempotency_key == idempotency_key,
        )
        return await self.session.scalar(stmt)

    async def get_by_artifact_key(self, artifact_key: str) -> TryOnJob | None:
        stmt = select(TryOnJob).where(TryOnJob.artifact_key == artifact_key)
        return await self.session.scalar(stmt)

    async def list_by_user(self, user_id: UUID, limit: int = 50) -> Sequence[TryOnJob]:
        stmt = (
            select(TryOnJob)
            .where(TryOnJob.user_id == user_id)
            .order_by(desc(TryOnJob.created_at))
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def update_status(
        self,
        job_id: UUID,
        status: str,
        failure_reason: str | None = None,
    ) -> TryOnJob | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = status
            job.failure_reason = failure_reason
            if status in ("completed", "failed", "cancelled"):
                job.completed_at = datetime.now(UTC)
            await self.flush()
        return job

    async def claim_next_job(
        self, worker_id: str, lease_seconds: int = 180
    ) -> TryOnJob | None:
        from datetime import timedelta
        now = datetime.now(UTC)
        stmt = (
            select(TryOnJob)
            .where(
                (TryOnJob.status == "queued")
                | (
                    (TryOnJob.status == "running")
                    & (TryOnJob.completed_at.is_(None))
                )
            )
            .order_by(TryOnJob.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = await self.session.scalar(stmt)
        if job:
            job.status = "running"
            await self.flush()
        return job


class TryOnArtifactRepository(BaseRepository[TryOnArtifact]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnArtifact)

    async def get_by_artifact_key(self, artifact_key: str) -> TryOnArtifact | None:
        stmt = select(TryOnArtifact).where(TryOnArtifact.artifact_key == artifact_key)
        return await self.session.scalar(stmt)

    async def get_by_job_id(self, job_id: UUID) -> TryOnArtifact | None:
        stmt = select(TryOnArtifact).where(TryOnArtifact.job_id == job_id)
        return await self.session.scalar(stmt)


class TryOnUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of work managing TryOn aggregate persistence."""

    def __init__(
        self,
        session_factory: (
            Callable[[], AsyncSession] | async_sessionmaker[AsyncSession] | None
        ) = None,
    ) -> None:
        super().__init__(session_factory)
        self._jobs: TryOnJobRepository | None = None
        self._artifacts: TryOnArtifactRepository | None = None

    async def __aenter__(self) -> "TryOnUnitOfWork":
        await super().__aenter__()
        self._jobs = None
        self._artifacts = None
        return self

    @property
    def jobs(self) -> TryOnJobRepository:
        if self._jobs is None:
            self._jobs = TryOnJobRepository(self.session)
        return self._jobs

    @property
    def artifacts(self) -> TryOnArtifactRepository:
        if self._artifacts is None:
            self._artifacts = TryOnArtifactRepository(self.session)
        return self._artifacts
