"""Unit tests for Worker Leases, Timeouts, Optimistic Concurrency, and Restart Recovery (Phase 07.5).

Covers WKR-001 through WKR-013.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from fashx.tryon.lifecycle.service import JobLifecycleService
from fashx.tryon.lifecycle.states import JobStatus
from fashx.tryon.lifecycle.timeout_policy import (
    DEFAULT_TIMEOUT_POLICY,
    LeaseLostError,
    StaleVersionError,
)


class MockJobRepository:
    def __init__(self, initial_job: SimpleNamespace) -> None:
        self.job = initial_job
        self.events: list[dict] = []

    async def get_by_id(self, job_id: object) -> SimpleNamespace | None:
        if self.job and self.job.id == job_id:
            return self.job
        return None

    async def claim_with_lease(
        self,
        job_id: object,
        worker_id: str,
        lease_token: object,
        lease_expires_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        if self.job.status not in ("QUEUED", "queued", "RETRY_PENDING", "retry_pending"):
            return False
        # If lease exists and is not expired, reject
        if self.job.lease_expires_at and self.job.lease_expires_at > now_ts:
            return False

        self.job.status = JobStatus.PROCESSING.value
        self.job.worker_id = worker_id
        self.job.locked_by = worker_id
        self.job.lease_token = lease_token
        self.job.lease_expires_at = lease_expires_at
        self.job.heartbeat_at = now_ts
        self.job.version += 1
        return True

    async def record_heartbeat(
        self,
        job_id: object,
        worker_id: str,
        lease_token: object,
        new_lease_expires_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        now_ts = now or datetime.now(UTC)
        if self.job.worker_id != worker_id or self.job.lease_token != lease_token:
            return False
        if self.job.lease_expires_at <= now_ts:
            return False  # Already expired, cannot renew
        self.job.heartbeat_at = now_ts
        self.job.lease_expires_at = new_lease_expires_at
        return True

    async def transition_with_version_and_event(
        self,
        job_id: object,
        expected_status: str,
        target_status: str,
        expected_version: int | None = None,
        worker_id: str | None = None,
        lease_token: object | None = None,
        actor_type: str = "WORKER",
        reason_code: str | None = None,
        metadata: dict | None = None,
        now: datetime | None = None,
    ) -> bool:
        if expected_version is not None and self.job.version != expected_version:
            return False
        if worker_id is not None and self.job.worker_id != worker_id:
            return False
        if lease_token is not None and self.job.lease_token != lease_token:
            return False

        self.job.status = target_status
        self.job.version += 1
        self.events.append({
            "job_id": job_id,
            "from_state": expected_status,
            "to_state": target_status,
            "reason_code": reason_code,
            "actor_type": actor_type,
        })
        return True


def make_test_job(status: str = "QUEUED", version: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        status=status,
        version=version,
        worker_id=None,
        locked_by=None,
        lease_token=None,
        lease_expires_at=None,
        heartbeat_at=None,
        retry_count=0,
        provider_job_id=None,
    )


async def test_worker_claims_queued_job_creates_lease() -> None:
    # WKR-001
    job = make_test_job(status="QUEUED")
    repo = MockJobRepository(job)
    service = JobLifecycleService(tryon_uow=SimpleNamespace(jobs=repo))

    lease = await service.claim_job_with_lease(
        job_id=job.id,
        worker_id="worker-node-1",
        lease_seconds=60,
    )
    assert lease is not None
    assert job.status == JobStatus.PROCESSING.value
    assert job.worker_id == "worker-node-1"
    assert job.version == 2
    assert not lease.is_expired()


async def test_second_worker_cannot_claim_active_lease() -> None:
    # WKR-002
    job = make_test_job(status="QUEUED")
    repo = MockJobRepository(job)
    service = JobLifecycleService(tryon_uow=SimpleNamespace(jobs=repo))

    lease1 = await service.claim_job_with_lease(job_id=job.id, worker_id="worker-1", lease_seconds=60)
    assert lease1 is not None

    # Second worker attempts to claim
    lease2 = await service.claim_job_with_lease(job_id=job.id, worker_id="worker-2", lease_seconds=60)
    assert lease2 is None
    assert job.worker_id == "worker-1"


async def test_heartbeat_renews_active_lease() -> None:
    # WKR-003
    job = make_test_job(status="QUEUED")
    repo = MockJobRepository(job)
    service = JobLifecycleService(tryon_uow=SimpleNamespace(jobs=repo))

    now = datetime.now(UTC)
    lease = await service.claim_job_with_lease(job_id=job.id, worker_id="worker-1", lease_seconds=60, now=now)
    assert lease is not None

    # Heartbeat after 20 seconds
    later = now + timedelta(seconds=20)
    new_expiry = later + timedelta(seconds=60)
    renewed = await repo.record_heartbeat(
        job_id=job.id,
        worker_id="worker-1",
        lease_token=lease.lease_token,
        new_lease_expires_at=new_expiry,
        now=later,
    )
    assert renewed is True
    assert job.lease_expires_at == new_expiry


async def test_expired_lease_allows_reclaim_and_blocks_old_worker() -> None:
    # WKR-004, WKR-005, WKR-006
    job = make_test_job(status="QUEUED")
    repo = MockJobRepository(job)
    service = JobLifecycleService(tryon_uow=SimpleNamespace(jobs=repo))

    t0 = datetime.now(UTC)
    old_lease = await service.claim_job_with_lease(job_id=job.id, worker_id="old-worker", lease_seconds=30, now=t0)
    assert old_lease is not None

    # Fast forward past lease expiry (t0 + 40s)
    t1 = t0 + timedelta(seconds=40)
    assert old_lease.is_expired(t1)

    # Old worker tries heartbeat on expired lease -> rejected (WKR-005)
    heartbeat_ok = await repo.record_heartbeat(
        job_id=job.id,
        worker_id="old-worker",
        lease_token=old_lease.lease_token,
        new_lease_expires_at=t1 + timedelta(seconds=30),
        now=t1,
    )
    assert heartbeat_ok is False

    # New worker reclaims job (WKR-004)
    job.status = "QUEUED"  # Sweeper reset
    new_lease = await service.claim_job_with_lease(job_id=job.id, worker_id="new-worker", lease_seconds=60, now=t1)
    assert new_lease is not None
    assert job.worker_id == "new-worker"

    # Old worker attempts to mark job completed -> rejected (WKR-006)
    with pytest.raises(LeaseLostError):
        await service.transition_job(
            job_id=job.id,
            expected_status=JobStatus.PROCESSING,
            target_status=JobStatus.OUTPUT_VALIDATING,
            expected_version=2,  # Stale version from old worker
            worker_id="old-worker",
            lease_token=old_lease.lease_token,
        )


async def test_stale_version_update_rejected() -> None:
    # STM-018
    job = make_test_job(status="PROCESSING", version=5)
    repo = MockJobRepository(job)
    service = JobLifecycleService(tryon_uow=SimpleNamespace(jobs=repo))

    with pytest.raises(StaleVersionError):
        await service.transition_job(
            job_id=job.id,
            expected_status=JobStatus.PROCESSING,
            target_status=JobStatus.OUTPUT_VALIDATING,
            expected_version=4,  # Outdated version
        )


def test_default_timeout_policy_values() -> None:
    # WKR-011
    assert DEFAULT_TIMEOUT_POLICY.worker_lease_seconds == 60
    assert DEFAULT_TIMEOUT_POLICY.worker_heartbeat_seconds == 15
    assert DEFAULT_TIMEOUT_POLICY.provider_inference_deadline_seconds == 180.0
    assert DEFAULT_TIMEOUT_POLICY.whole_job_deadline_seconds == 300.0
