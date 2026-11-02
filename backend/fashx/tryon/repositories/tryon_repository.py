from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.tryon import TryOnArtifact, TryOnJob, TryOnUsage
from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork


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

    async def get_owned(self, job_id: UUID, user_id: UUID) -> TryOnJob | None:
        stmt = select(TryOnJob).where(
            TryOnJob.id == job_id,
            TryOnJob.user_id == user_id,
        )
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

    async def create(
        self,
        *,
        user_id: UUID,
        garment_id: UUID,
        idempotency_key: str,
        artifact_key: str,
        model_version: str,
        pipeline_version: str,
        profile_photo_id: UUID | None = None,
        photo_version: int = 1,
        garment_version: int = 1,
        configuration_hash: str = "default",
        queue_name: str = "tryon-jobs",
        provider: str | None = None,
        id_: UUID | None = None,
    ) -> TryOnJob:
        existing = await self.get_by_user_and_idempotency(user_id, idempotency_key)
        if existing:
            return existing
        job = TryOnJob(
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=profile_photo_id,
            idempotency_key=idempotency_key,
            artifact_key=artifact_key,
            status="queued",
            model_version=model_version,
            pipeline_version=pipeline_version,
            photo_version=photo_version,
            garment_version=garment_version,
            configuration_hash=configuration_hash,
            queue_name=queue_name,
            provider=provider,
            attempts=1,
            attempt_count=0,
            cancel_requested=False,
        )
        if id_ is not None:
            job.id = id_
        self.add(job)
        await self.flush()
        return job

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
                job.locked_at = None
                job.locked_by = None
            await self.flush()
        return job

    async def set_provider_job(
        self,
        job_id: UUID,
        provider: str,
        provider_job_id: str,
    ) -> TryOnJob | None:
        job = await self.get_by_id(job_id)
        if job:
            job.provider = provider
            job.provider_job_id = provider_job_id
            await self.flush()
        return job

    async def requeue(
        self,
        job_id: UUID,
        delay_s: float = 0.0,
        clear_provider_job: bool = False,
    ) -> TryOnJob | None:
        job = await self.get_by_id(job_id)
        if job:
            job.status = "queued"
            job.attempts += 1
            job.locked_at = None
            job.locked_by = None
            if clear_provider_job:
                job.provider_job_id = None
            await self.flush()
        return job

    async def fail(
        self,
        job_id: UUID,
        error_code: str,
        user_message: str | None = None,
    ) -> TryOnJob | None:
        return await self.update_status(job_id, "failed", failure_reason=error_code)

    async def cancel(
        self,
        job_id: UUID,
        reason: str = "cancelled",
    ) -> TryOnJob | None:
        return await self.update_status(job_id, "cancelled", failure_reason=reason)

    async def request_cancel(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> TryOnJob | None:
        job = await self.get_owned(job_id, user_id)
        if job:
            job.cancel_requested = True
            if job.status == "queued":
                job.status = "cancelled"
                job.failure_reason = "cancelled_by_user"
                job.completed_at = datetime.now(UTC)
                job.locked_at = None
                job.locked_by = None
            await self.flush()
        return job

    async def complete(
        self,
        job_id: UUID,
        media_id: UUID | None = None,
    ) -> TryOnJob | None:
        return await self.update_status(job_id, "completed")

    async def claim_next_job(self, worker_id: str, lease_seconds: int = 180) -> TryOnJob | None:
        now = datetime.now(UTC)
        expired_before = now - timedelta(seconds=lease_seconds)
        stmt = (
            select(TryOnJob)
            .where(
                or_(
                    TryOnJob.status == "queued",
                    and_(
                        TryOnJob.status == "running",
                        TryOnJob.completed_at.is_(None),
                        TryOnJob.locked_at.is_not(None),
                        TryOnJob.locked_at < expired_before,
                    ),
                )
            )
            .order_by(TryOnJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = await self.session.scalar(stmt)
        if job:
            job.status = "running"
            job.locked_at = now
            job.locked_by = worker_id
            job.attempt_count += 1
            await self.flush()
        return job

    async def renew_lease(
        self,
        job_id: UUID,
        worker_id: str,
        lease_seconds: int = 180,
    ) -> bool:
        job = await self.get_by_id(job_id)
        if job and job.status == "running" and job.locked_by == worker_id:
            job.locked_at = datetime.now(UTC)
            await self.flush()
            return True
        return False

    async def release_lease(
        self,
        job_id: UUID,
        worker_id: str,
    ) -> bool:
        job = await self.get_by_id(job_id)
        if job and job.locked_by == worker_id:
            job.locked_at = None
            job.locked_by = None
            await self.flush()
            return True
        return False


class TryOnArtifactRepository(BaseRepository[TryOnArtifact]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnArtifact)

    async def get_by_artifact_key(self, artifact_key: str) -> TryOnArtifact | None:
        stmt = select(TryOnArtifact).where(TryOnArtifact.artifact_key == artifact_key)
        return await self.session.scalar(stmt)

    async def get_by_job_id(self, job_id: UUID) -> TryOnArtifact | None:
        stmt = select(TryOnArtifact).where(TryOnArtifact.job_id == job_id)
        return await self.session.scalar(stmt)


class TryOnUsageRepository(BaseRepository[TryOnUsage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnUsage)

    async def record(
        self,
        outcome: str,
        *,
        provider: str = "fashn_api",
        model: str = "tryon-v1.6",
        error_code: str | None = None,
        latency_ms: int | None = None,
        cost_usd_est: float | None = None,
    ) -> TryOnUsage:
        usage = TryOnUsage(
            provider=provider,
            model=model,
            outcome=outcome,
            error_code=error_code,
            latency_ms=latency_ms,
            cost_usd_est=Decimal(str(cost_usd_est)) if cost_usd_est is not None else None,
        )
        self.add(usage)
        await self.flush()
        return usage


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
        self._usage: TryOnUsageRepository | None = None

    async def __aenter__(self) -> "TryOnUnitOfWork":
        await super().__aenter__()
        self._jobs = None
        self._artifacts = None
        self._usage = None
        return self

    @property
    def jobs(self) -> TryOnJobRepository:
        if self._jobs is None:
            self._jobs = TryOnJobRepository(self.session)
        return self._jobs

    @property
    def tryon(self) -> TryOnJobRepository:
        return self.jobs

    @property
    def artifacts(self) -> TryOnArtifactRepository:
        if self._artifacts is None:
            self._artifacts = TryOnArtifactRepository(self.session)
        return self._artifacts

    @property
    def usage(self) -> TryOnUsageRepository:
        if self._usage is None:
            self._usage = TryOnUsageRepository(self.session)
        return self._usage
