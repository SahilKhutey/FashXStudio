from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.settings import get_settings
from database.models.tryon import TryOnArtifact, TryOnJob


class TryOnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id_for_user(self, *, user_id: UUID, job_id: UUID) -> TryOnJob | None:
        stmt = select(TryOnJob).where(TryOnJob.user_id == user_id, TryOnJob.id == job_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_idempotency(self, *, user_id: UUID, key: str) -> TryOnJob | None:
        stmt = select(TryOnJob).where(TryOnJob.user_id == user_id, TryOnJob.idempotency_key == key)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_artifact_key(self, artifact_key: str) -> TryOnJob | None:
        stmt = select(TryOnJob).where(TryOnJob.artifact_key == artifact_key)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_job(self, **values) -> TryOnJob:
        job = TryOnJob(**values)
        self.session.add(job)
        await self.session.flush()
        return job

    async def create_or_get_artifact(self, **values) -> TryOnArtifact:
        artifact = TryOnArtifact(**values)
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def get_artifact_for_job(self, job_id: UUID) -> TryOnArtifact | None:
        stmt = select(TryOnArtifact).where(TryOnArtifact.job_id == job_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def claim_job(self, job_id: UUID) -> TryOnJob | None:
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=get_settings().tryon_lock_timeout_seconds)
        eligible = or_(
            TryOnJob.status == "queued",
            and_(TryOnJob.status == "processing", TryOnJob.locked_at.is_not(None), TryOnJob.locked_at < stale_before),
        )
        result = await self.session.execute(
            update(TryOnJob)
            .where(TryOnJob.id == job_id, eligible, TryOnJob.cancel_requested.is_(False))
            .values(
                status="processing",
                attempt_count=TryOnJob.attempt_count + 1,
                locked_at=now,
                last_error=None,
            )
            .returning(TryOnJob.id)
        )
        claimed = result.scalar_one_or_none()
        if claimed is None:
            return None
        return await self.session.get(TryOnJob, claimed)

    async def update_processing(self, job: TryOnJob, *, status: str) -> None:
        job.status = status
        await self.session.flush()

    async def get_by_id(self, job_id: UUID) -> TryOnJob | None:
        return await self.session.get(TryOnJob, job_id)

    async def complete(self, job: TryOnJob, *, result_key: str, quality: dict) -> TryOnArtifact:
        artifact = TryOnArtifact(
            job_id=job.id,
            artifact_key=job.artifact_key,
            result_key=result_key,
            model_version=job.model_version,
            pipeline_version=job.pipeline_version,
            photo_version=job.photo_version,
            garment_version=job.garment_version,
            quality_status=quality["quality_status"],
            quality_score=quality.get("quality_score"),
            width=quality.get("width"),
            height=quality.get("height"),
            size_bytes=quality.get("size_bytes"),
            content_type=quality.get("content_type"),
            content_sha256=quality.get("content_sha256"),
            quality_reasons=quality.get("quality_reasons"),
        )
        self.session.add(artifact)
        job.status = "completed"
        job.locked_at = None
        job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return artifact

    async def fail(self, job: TryOnJob, *, reason: str, retryable: bool) -> bool:
        settings = get_settings()
        job.failure_reason = reason
        job.last_error = reason
        job.locked_at = None
        should_retry = retryable and job.attempt_count < settings.tryon_max_attempts and not job.cancel_requested
        if should_retry:
            job.status = "queued"
        else:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return should_retry

    async def cancel(self, job: TryOnJob) -> None:
        if job.status in {"completed", "failed", "cancelled"}:
            return
        job.cancel_requested = True
        job.status = "cancelled"
        job.locked_at = None
        job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
