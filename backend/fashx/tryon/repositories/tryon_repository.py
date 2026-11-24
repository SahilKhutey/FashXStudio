from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.tryon import (
    TryOnArtifact,
    TryOnDeadLetter,
    TryOnInputAuthorizationSnapshot,
    TryOnInputValidation,
    TryOnJob,
    TryOnJobEvent,
    TryOnProviderAttempt,
    TryOnUsage,
)
from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork
from fashx.tryon.domain.state_machine import validate_transition


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
        request_hash: str | None = None,
        validation_policy_version: str | None = None,
        progress_stage: str | None = "waiting_for_worker",
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
            request_hash=request_hash,
            validation_policy_version=validation_policy_version,
            progress_stage=progress_stage,
            attempts=1,
            attempt_count=0,
            cancel_requested=False,
        )
        if id_ is not None:
            job.id = id_
        self.add(job)
        await self.flush()
        return job

    async def transition_if_owned(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        expected_status: str,
        new_status: str,
        progress_stage: str | None = None,
        failure_reason: str | None = None,
        error_code: str | None = None,
    ) -> bool:
        """Atomically transitions job state if owned by current worker. Prevents stale worker overwrites."""
        validate_transition(expected_status, new_status)

        values: dict[str, object] = {
            "status": new_status,
            "updated_at": datetime.now(UTC),
        }
        if progress_stage:
            values["progress_stage"] = progress_stage
        if failure_reason:
            values["failure_reason"] = failure_reason
        if error_code:
            values["error_code"] = error_code
        if new_status in ("completed", "failed", "cancelled", "blocked_by_permission"):
            values["completed_at"] = datetime.now(UTC)
            values["locked_by"] = None
            values["locked_at"] = None
            values["lock_expires_at"] = None

        stmt = (
            update(TryOnJob)
            .where(
                TryOnJob.id == job_id,
                TryOnJob.locked_by == worker_id,
                TryOnJob.status == expected_status,
            )
            .values(**values)
        )
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1

    async def transition_with_version_and_event(
        self,
        job_id: UUID,
        expected_status: str,
        target_status: str,
        expected_version: int | None = None,
        worker_id: str | None = None,
        lease_token: UUID | None = None,
        actor_type: str = "WORKER",
        reason_code: str | None = None,
        metadata: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> bool:
        from uuid import uuid4
        now_ts = now or datetime.now(UTC)
        values: dict[str, object] = {
            "status": target_status,
            "updated_at": now_ts,
            "version": TryOnJob.version + 1,
        }
        if target_status.lower() in ("completed", "failed", "cancelled", "expired"):
            values["completed_at"] = now_ts
            values["locked_by"] = None
            values["locked_at"] = None
            values["lock_expires_at"] = None
            values["worker_id"] = None
            values["lease_token"] = None
            values["lease_expires_at"] = None
            if target_status.lower() == "failed":
                values["failed_at"] = now_ts

        conditions = [
            TryOnJob.id == job_id,
            or_(
                TryOnJob.status == expected_status,
                TryOnJob.status == expected_status.lower(),
                TryOnJob.status == expected_status.upper(),
            ),
        ]
        if expected_version is not None:
            conditions.append(TryOnJob.version == expected_version)
        if worker_id is not None:
            conditions.append(or_(TryOnJob.worker_id == worker_id, TryOnJob.locked_by == worker_id))
        if lease_token is not None:
            conditions.append(TryOnJob.lease_token == lease_token)

        stmt = update(TryOnJob).where(and_(*conditions)).values(**values)
        res = await self.session.execute(stmt)
        if res.rowcount != 1:
            return False

        event = TryOnJobEvent(
            id=uuid4(),
            job_id=job_id,
            from_state=expected_status,
            to_state=target_status,
            event_type="JOB_STATE_TRANSITION",
            reason_code=reason_code,
            actor_type=actor_type,
            worker_id=worker_id,
            metadata_json=metadata or {},
            created_at=now_ts,
        )
        self.session.add(event)
        await self.flush()
        return True

    async def claim_with_lease(
        self,
        job_id: UUID,
        worker_id: str,
        lease_token: UUID,
        lease_expires_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        stmt = (
            update(TryOnJob)
            .where(
                TryOnJob.id == job_id,
                or_(
                    TryOnJob.status == "queued",
                    TryOnJob.status == "QUEUED",
                    TryOnJob.status == "retry_pending",
                    TryOnJob.status == "RETRY_PENDING",
                ),
                or_(
                    TryOnJob.lease_expires_at.is_(None),
                    TryOnJob.lease_expires_at < now_ts,
                    TryOnJob.lock_expires_at.is_(None),
                    TryOnJob.lock_expires_at < now_ts,
                ),
            )
            .values(
                status="PROCESSING",
                worker_id=worker_id,
                locked_by=worker_id,
                lease_token=lease_token,
                lease_expires_at=lease_expires_at,
                lock_expires_at=lease_expires_at,
                heartbeat_at=now_ts,
                locked_at=now_ts,
                version=TryOnJob.version + 1,
                updated_at=now_ts,
            )
        )
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1

    async def record_heartbeat(
        self,
        job_id: UUID,
        worker_id: str,
        lease_token: UUID,
        new_lease_expires_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        stmt = (
            update(TryOnJob)
            .where(
                TryOnJob.id == job_id,
                or_(TryOnJob.worker_id == worker_id, TryOnJob.locked_by == worker_id),
                TryOnJob.lease_token == lease_token,
                or_(
                    TryOnJob.lease_expires_at > now_ts,
                    TryOnJob.lock_expires_at > now_ts,
                ),
            )
            .values(
                heartbeat_at=now_ts,
                lease_expires_at=new_lease_expires_at,
                lock_expires_at=new_lease_expires_at,
                updated_at=now_ts,
            )
        )
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1

    async def update_retry_pending(
        self,
        job_id: UUID,
        retry_count: int,
        next_retry_at: datetime,
        last_error_code: str | None = None,
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        stmt = (
            update(TryOnJob)
            .where(TryOnJob.id == job_id)
            .values(
                status="RETRY_PENDING",
                retry_count=retry_count,
                next_retry_at=next_retry_at,
                last_error_code=last_error_code,
                last_error_at=now_ts,
                worker_id=None,
                locked_by=None,
                lease_token=None,
                lease_expires_at=None,
                lock_expires_at=None,
                version=TryOnJob.version + 1,
                updated_at=now_ts,
            )
        )
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1

    async def update_status_and_event(
        self,
        job_id: UUID,
        expected_status: str,
        new_status: str,
        actor_type: str = "SYSTEM",
        actor_id: str | None = None,
        reason_code: str | None = None,
        metadata: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> bool:
        from uuid import uuid4
        now_ts = now or datetime.now(UTC)
        values: dict[str, object] = {
            "status": new_status,
            "version": TryOnJob.version + 1,
            "updated_at": now_ts,
        }
        if new_status.upper() in ("COMPLETED", "FAILED", "CANCELLED", "EXPIRED"):
            values["completed_at"] = now_ts
            values["locked_by"] = None
            values["worker_id"] = None
            values["lease_token"] = None
            values["lease_expires_at"] = None
            values["lock_expires_at"] = None
            if new_status.upper() == "FAILED":
                values["failed_at"] = now_ts
            elif new_status.upper() == "CANCELLED":
                values["cancel_requested_at"] = now_ts

        stmt = (
            update(TryOnJob)
            .where(
                TryOnJob.id == job_id,
                or_(
                    TryOnJob.status == expected_status,
                    TryOnJob.status == expected_status.lower(),
                    TryOnJob.status == expected_status.upper(),
                ),
            )
            .values(**values)
        )
        res = await self.session.execute(stmt)
        if res.rowcount != 1:
            return False

        event = TryOnJobEvent(
            id=uuid4(),
            job_id=job_id,
            from_state=expected_status,
            to_state=new_status,
            event_type="JOB_STATUS_UPDATE",
            reason_code=reason_code,
            actor_type=actor_type,
            worker_id=actor_id,
            metadata_json=metadata or {},
            created_at=now_ts,
        )
        self.session.add(event)
        await self.flush()
        return True

    async def find_recovery_candidates(
        self,
        now: datetime | None = None,
        limit: int = 100,
    ) -> list[TryOnJob]:
        terminal = ["completed", "COMPLETED", "failed", "FAILED", "cancelled", "CANCELLED", "expired", "EXPIRED"]
        stmt = (
            select(TryOnJob)
            .where(TryOnJob.status.not_in(terminal))
            .order_by(TryOnJob.created_at.asc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def schedule_recovery(
        self,
        job_id: UUID,
        reason: str = "WORKER_LEASE_EXPIRED",
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        stmt = (
            update(TryOnJob)
            .where(TryOnJob.id == job_id)
            .values(
                status="QUEUED",
                worker_id=None,
                locked_by=None,
                lease_token=None,
                lease_expires_at=None,
                lock_expires_at=None,
                version=TryOnJob.version + 1,
                updated_at=now_ts,
            )
        )
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1

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


class TryOnInputValidationRepository(BaseRepository[TryOnInputValidation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnInputValidation)

    async def get_by_job_id(self, job_id: UUID) -> Sequence[TryOnInputValidation]:
        stmt = select(TryOnInputValidation).where(TryOnInputValidation.tryon_job_id == job_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def record_validation(
        self,
        *,
        tryon_job_id: UUID,
        role: str,
        asset_id: UUID,
        asset_version: str,
        policy_version: str,
        status: str,
        original_sha256: str | None = None,
        normalized_sha256: str | None = None,
        technical_metadata: dict | None = None,
        visual_metadata: dict | None = None,
        issues: list | None = None,
        validated_at: datetime | None = None,
    ) -> TryOnInputValidation:
        record = TryOnInputValidation(
            tryon_job_id=tryon_job_id,
            role=role,
            asset_id=asset_id,
            asset_version=asset_version,
            policy_version=policy_version,
            status=status,
            original_sha256=original_sha256,
            normalized_sha256=normalized_sha256,
            technical_metadata=technical_metadata or {},
            visual_metadata=visual_metadata or {},
            issues=issues or [],
            validated_at=validated_at or datetime.now(UTC),
        )
        self.add(record)
        await self.flush()
        return record


class TryOnInputAuthorizationSnapshotRepository(BaseRepository[TryOnInputAuthorizationSnapshot]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnInputAuthorizationSnapshot)

    async def get_by_job_id(self, job_id: UUID) -> Sequence[TryOnInputAuthorizationSnapshot]:
        stmt = select(TryOnInputAuthorizationSnapshot).where(
            TryOnInputAuthorizationSnapshot.tryon_job_id == job_id
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def record_snapshot(
        self,
        *,
        tryon_job_id: UUID,
        authorization_type: str,
        subject_id: UUID,
        permission_scope: str,
        policy_version: str,
        result: str,
        evidence_revision: str | None = None,
    ) -> TryOnInputAuthorizationSnapshot:
        snapshot = TryOnInputAuthorizationSnapshot(
            tryon_job_id=tryon_job_id,
            authorization_type=authorization_type,
            subject_id=subject_id,
            permission_scope=permission_scope,
            policy_version=policy_version,
            result=result,
            evidence_revision=evidence_revision,
        )
        self.add(snapshot)
        await self.flush()
        return snapshot


class TryOnProviderAttemptRepository(BaseRepository[TryOnProviderAttempt]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnProviderAttempt)

    async def get_by_job_id(self, job_id: UUID) -> Sequence[TryOnProviderAttempt]:
        stmt = (
            select(TryOnProviderAttempt)
            .where(TryOnProviderAttempt.job_id == job_id)
            .order_by(TryOnProviderAttempt.attempt_number.asc())
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def get_latest_attempt(self, job_id: UUID) -> TryOnProviderAttempt | None:
        stmt = (
            select(TryOnProviderAttempt)
            .where(TryOnProviderAttempt.job_id == job_id)
            .order_by(desc(TryOnProviderAttempt.attempt_number))
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def create_attempt(
        self,
        *,
        job_id: UUID,
        attempt_number: int,
        provider: str,
        model_version: str,
        status: str,
        request_hash: str,
        provider_job_id: str | None = None,
    ) -> TryOnProviderAttempt:
        attempt = TryOnProviderAttempt(
            job_id=job_id,
            attempt_number=attempt_number,
            provider=provider,
            model_version=model_version,
            status=status,
            request_hash=request_hash,
            provider_job_id=provider_job_id,
        )
        self.add(attempt)
        await self.flush()
        return attempt

    async def update_status(
        self,
        attempt_id: UUID,
        status: str,
        *,
        provider_job_id: str | None = None,
        provider_error_code: str | None = None,
        safe_error_detail: str | None = None,
        submitted_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> TryOnProviderAttempt | None:
        attempt = await self.get_by_id(attempt_id)
        if attempt:
            attempt.status = status
            if provider_job_id is not None:
                attempt.provider_job_id = provider_job_id
            if provider_error_code is not None:
                attempt.provider_error_code = provider_error_code
            if safe_error_detail is not None:
                attempt.safe_error_detail = safe_error_detail
            if submitted_at is not None:
                attempt.submitted_at = submitted_at
            if completed_at is not None:
                attempt.completed_at = completed_at
            await self.flush()
        return attempt


class TryOnJobEventRepository(BaseRepository[TryOnJobEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnJobEvent)

    async def get_by_job_id(self, job_id: UUID) -> list[TryOnJobEvent]:
        stmt = (
            select(TryOnJobEvent)
            .where(TryOnJobEvent.job_id == job_id)
            .order_by(TryOnJobEvent.created_at.asc())
        )
        res = await self.session.scalars(stmt)
        return list(res.all())


class TryOnDeadLetterRepository(BaseRepository[TryOnDeadLetter]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnDeadLetter)

    async def create_dead_letter(self, record: Any) -> TryOnDeadLetter:
        dlq = TryOnDeadLetter(
            id=record.id,
            job_id=record.job_id,
            source=record.source,
            failure_stage=record.failure_stage,
            error_code=record.error_code,
            error_summary=record.error_summary,
            attempt_number=record.attempt_number,
            original_message_id=record.original_message_id,
            payload_reference=record.payload_reference,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            created_at=record.created_at,
        )
        self.session.add(dlq)
        await self.flush()
        return dlq

    async def update_dlq_status(
        self,
        dead_letter_id: UUID,
        status: str,
        resolved_by: str | None = None,
        resolution_note: str | None = None,
        resolved_at: datetime | None = None,
    ) -> bool:
        values: dict[str, object] = {"status": status}
        if resolved_by:
            values["resolved_by"] = resolved_by
        if resolution_note:
            values["resolution_note"] = resolution_note
        if resolved_at:
            values["resolved_at"] = resolved_at

        stmt = update(TryOnDeadLetter).where(TryOnDeadLetter.id == dead_letter_id).values(**values)
        res = await self.session.execute(stmt)
        await self.flush()
        return res.rowcount == 1


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
        self._validations: TryOnInputValidationRepository | None = None
        self._auth_snapshots: TryOnInputAuthorizationSnapshotRepository | None = None
        self._provider_attempts: TryOnProviderAttemptRepository | None = None
        self._events: TryOnJobEventRepository | None = None
        self._dead_letters: TryOnDeadLetterRepository | None = None

    async def __aenter__(self) -> "TryOnUnitOfWork":
        await super().__aenter__()
        self._jobs = None
        self._artifacts = None
        self._usage = None
        self._validations = None
        self._auth_snapshots = None
        self._provider_attempts = None
        self._events = None
        self._dead_letters = None
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

    @property
    def validations(self) -> TryOnInputValidationRepository:
        if self._validations is None:
            self._validations = TryOnInputValidationRepository(self.session)
        return self._validations

    @property
    def auth_snapshots(self) -> TryOnInputAuthorizationSnapshotRepository:
        if self._auth_snapshots is None:
            self._auth_snapshots = TryOnInputAuthorizationSnapshotRepository(self.session)
        return self._auth_snapshots

    @property
    def provider_attempts(self) -> TryOnProviderAttemptRepository:
        if self._provider_attempts is None:
            self._provider_attempts = TryOnProviderAttemptRepository(self.session)
        return self._provider_attempts

    @property
    def events(self) -> TryOnJobEventRepository:
        if self._events is None:
            self._events = TryOnJobEventRepository(self.session)
        return self._events

    @property
    def dead_letters(self) -> TryOnDeadLetterRepository:
        if self._dead_letters is None:
            self._dead_letters = TryOnDeadLetterRepository(self.session)
        return self._dead_letters
