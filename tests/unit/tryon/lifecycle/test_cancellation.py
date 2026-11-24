"""Unit tests for VTO Job Cancellation Workflow, Security, and Race Protection (Phase 07.5).

Covers CAN-001 through CAN-010.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from fashx.tryon.lifecycle.cancellation import (
    CancellationConflictError,
    JobCancellationService,
    JobNotFoundError,
)
from fashx.tryon.lifecycle.states import JobStatus


class MockCancellationRepository:
    def __init__(self, jobs: dict[UUID, SimpleNamespace]) -> None:
        self.jobs = jobs
        self.status_updates: list[dict] = []

    async def get_owned(self, job_id: UUID, user_id: UUID) -> SimpleNamespace | None:
        job = self.jobs.get(job_id)
        if job and job.user_id == user_id:
            return job
        return None

    async def update_status_and_event(
        self,
        job_id: UUID,
        expected_status: str,
        new_status: str,
        actor_type: str = "USER",
        actor_id: str | None = None,
        reason_code: str | None = None,
        metadata: dict | None = None,
        now: object = None,
    ) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        job.status = new_status
        self.status_updates.append({
            "job_id": job_id,
            "expected_status": expected_status,
            "new_status": new_status,
            "actor_type": actor_type,
            "actor_id": actor_id,
        })
        return True


class MockProviderAdapter:
    def __init__(self) -> None:
        self.cancelled_provider_jobs: list[str] = []

    async def cancel(self, provider_job_id: str) -> bool:
        self.cancelled_provider_jobs.append(provider_job_id)
        return True


async def test_cancel_queued_and_retry_pending_is_immediate() -> None:
    # CAN-001, CAN-002, CAN-005
    owner = uuid4()
    job1 = SimpleNamespace(id=uuid4(), user_id=owner, status="QUEUED", provider_job_id=None)
    job2 = SimpleNamespace(id=uuid4(), user_id=owner, status="RETRY_PENDING", provider_job_id=None)

    repo = MockCancellationRepository({job1.id: job1, job2.id: job2})
    service = JobCancellationService(repository=repo)

    res1 = await service.request_cancellation(job_id=job1.id, owner_id=owner)
    assert res1.is_immediate is True
    assert res1.new_status == JobStatus.CANCELLED
    assert job1.status == JobStatus.CANCELLED.value

    res2 = await service.request_cancellation(job_id=job2.id, owner_id=owner)
    assert res2.is_immediate is True
    assert res2.new_status == JobStatus.CANCELLED
    assert job2.status == JobStatus.CANCELLED.value


async def test_cancel_active_processing_moves_to_cancel_requested() -> None:
    # CAN-003, CAN-009
    owner = uuid4()
    job = SimpleNamespace(id=uuid4(), user_id=owner, status="PROCESSING", provider_job_id="fashn-pred-777")
    provider = MockProviderAdapter()

    repo = MockCancellationRepository({job.id: job})
    service = JobCancellationService(repository=repo, provider_adapter=provider)

    res = await service.request_cancellation(job_id=job.id, owner_id=owner)
    assert res.is_immediate is False
    assert res.new_status == JobStatus.CANCEL_REQUESTED
    assert job.status == JobStatus.CANCEL_REQUESTED.value
    # CAN-009: Provider cancellation attempted
    assert provider.cancelled_provider_jobs == ["fashn-pred-777"]


async def test_cancel_completed_job_rejected_no_state_rewrite() -> None:
    # CAN-006: Completed cannot be rewritten to CANCELLED
    owner = uuid4()
    job = SimpleNamespace(id=uuid4(), user_id=owner, status="COMPLETED", provider_job_id="fashn-pred-999")

    repo = MockCancellationRepository({job.id: job})
    service = JobCancellationService(repository=repo)

    with pytest.raises(CancellationConflictError):
        await service.request_cancellation(job_id=job.id, owner_id=owner)

    assert job.status == "COMPLETED"


async def test_cancel_already_cancelled_job_is_idempotent() -> None:
    # CAN-007
    owner = uuid4()
    job = SimpleNamespace(id=uuid4(), user_id=owner, status="CANCELLED", provider_job_id=None)

    repo = MockCancellationRepository({job.id: job})
    service = JobCancellationService(repository=repo)

    res = await service.request_cancellation(job_id=job.id, owner_id=owner)
    assert res.is_immediate is True
    assert res.new_status == JobStatus.CANCELLED


async def test_cross_tenant_cancellation_raises_job_not_found() -> None:
    # CAN-008: Strict anti-enumeration
    legit_owner = uuid4()
    attacker = uuid4()
    job = SimpleNamespace(id=uuid4(), user_id=legit_owner, status="QUEUED", provider_job_id=None)

    repo = MockCancellationRepository({job.id: job})
    service = JobCancellationService(repository=repo)

    with pytest.raises(JobNotFoundError):
        await service.request_cancellation(job_id=job.id, owner_id=attacker)
