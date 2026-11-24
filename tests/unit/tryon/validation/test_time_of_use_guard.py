"""Unit tests for Time-of-Use guard and VTO validation gate integration (Phase 07.3)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
from fashx.tryon.validation.contracts import (
    CombinedValidationResult,
    ImageRole,
    ImageValidationResult,
    Severity,
    ValidationIssue,
    ValidationStatus,
)
from fashx.tryon.validation.error_codes import VTO_CONSENT_REQUIRED


def make_dummy_jpeg() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (600, 800), color="blue").save(buf, format="JPEG")
    return buf.getvalue()


class FakeValidationRepo:
    def __init__(self) -> None:
        self.records: list[dict] = []

    async def record_validation(self, **kwargs: object) -> object:
        self.records.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeAuthSnapshotRepo:
    def __init__(self) -> None:
        self.snapshots: list[dict] = []

    async def record_snapshot(self, **kwargs: object) -> object:
        self.snapshots.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeTryOnJobRepo:
    def __init__(self, job: object) -> None:
        self.job = job
        self.failed_with: tuple | None = None
        self.cancelled_with: str | None = None

    async def get_by_id(self, job_id: object) -> object | None:
        return self.job

    async def fail(self, job_id: object, reason: str, user_message: str | None = None) -> None:
        self.failed_with = (job_id, reason, user_message)

    async def cancel(self, job_id: object, reason: str) -> None:
        self.cancelled_with = reason

    async def update_status(self, job_id: object, status: str, failure_reason: str | None = None) -> None:
        self.job.status = status


class FakeTryOnUoW:
    def __init__(self, job: object) -> None:
        self.jobs = FakeTryOnJobRepo(job)
        self.validations = FakeValidationRepo()
        self.auth_snapshots = FakeAuthSnapshotRepo()

    async def __aenter__(self) -> FakeTryOnUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def commit(self) -> None:
        pass


class FakeCatalogUoW:
    def __init__(self, garment: object | None = None) -> None:
        async def fake_get_by_id(gid: object) -> object:
            return garment or SimpleNamespace(
                id=gid, category="tops", source_id=uuid4(), status="ACTIVE"
            )

        self.garments = SimpleNamespace(get_by_id=fake_get_by_id)
        self.canonical_garments = self.garments

    async def __aenter__(self) -> FakeCatalogUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


class FakeProfileUoW:
    def __init__(self, has_consent: bool = True) -> None:
        self._has_consent = has_consent

    async def __aenter__(self) -> FakeProfileUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    @property
    def consents(self) -> object:
        async def has_consent(user_id: object, purpose: str) -> bool:
            return self._has_consent

        return SimpleNamespace(has_consent=has_consent)


class FakeAdapter:
    def __init__(self) -> None:
        self.submit_called = False

    def submit(self, req: object) -> str:
        self.submit_called = True
        return "provider-job-123"

    def collect(self, job_id: str, deadline_s: float) -> object:
        return SimpleNamespace(image_bytes=b"dummy", latency_ms=10, cost_usd_est=0.075, model="m", provider="p")


@pytest.mark.asyncio
async def test_vto_worker_blocks_provider_submission_when_validation_fails() -> None:
    job_id = uuid4()
    user_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        garment_id=uuid4(),
        status="queued",
        artifact_key=f"artifacts/{job_id}.jpg",
    )

    tryon_uow = FakeTryOnUoW(job)
    profile_uow = FakeProfileUoW(has_consent=True)
    adapter = FakeAdapter()

    # Create mock validator returning REJECTED
    rejected_shopper = ImageValidationResult(
        role=ImageRole.SHOPPER,
        status=ValidationStatus.REJECTED,
        asset_id=str(uuid4()),
        asset_version="v1",
        policy_version="v1",
        issues=[
            ValidationIssue(
                code=VTO_CONSENT_REQUIRED,
                severity=Severity.ERROR,
                message="Consent required",
                user_message="Please grant VTO consent",
            )
        ],
    )
    passed_garment = ImageValidationResult(
        role=ImageRole.GARMENT,
        status=ValidationStatus.PASSED,
        asset_id=str(uuid4()),
        asset_version="v1",
        policy_version="v1",
    )
    comb_result = CombinedValidationResult(
        status=ValidationStatus.REJECTED,
        shopper=rejected_shopper,
        garment=passed_garment,
    )

    class MockValidatorService:
        async def validate_and_record(self, **kwargs: object) -> CombinedValidationResult:
            return comb_result

    uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,  # type: ignore[arg-type]
        profile_uow=profile_uow,  # type: ignore[arg-type]
        catalog_uow=FakeCatalogUoW(),  # type: ignore[arg-type]
        adapter=adapter,
        validation_service=MockValidatorService(),
    )

    dummy_jpeg = make_dummy_jpeg()
    res = await uc.execute(
        job_id=job_id,
        user_photo_bytes=dummy_jpeg,
        garment_image_bytes=dummy_jpeg,
    )

    assert res.status == "failed"
    assert res.failure_reason == VTO_CONSENT_REQUIRED
    # CRITICAL: Provider adapter submit must NOT have been called!
    assert adapter.submit_called is False
    assert tryon_uow.jobs.failed_with is not None
    assert tryon_uow.jobs.failed_with[1] == VTO_CONSENT_REQUIRED


@pytest.mark.asyncio
async def test_vto_worker_time_of_use_recheck_blocks_revoked_consent() -> None:
    job_id = uuid4()
    user_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        garment_id=uuid4(),
        status="queued",
        artifact_key=f"artifacts/{job_id}.jpg",
    )

    tryon_uow = FakeTryOnUoW(job)
    # Consent was granted at validation time, but revoked right before inference!
    profile_uow = FakeProfileUoW(has_consent=False)
    adapter = FakeAdapter()

    passed_shopper = ImageValidationResult(
        role=ImageRole.SHOPPER,
        status=ValidationStatus.PASSED,
        asset_id=str(uuid4()),
        asset_version="v1",
        policy_version="v1",
    )
    passed_garment = ImageValidationResult(
        role=ImageRole.GARMENT,
        status=ValidationStatus.PASSED,
        asset_id=str(uuid4()),
        asset_version="v1",
        policy_version="v1",
    )
    comb_result = CombinedValidationResult(
        status=ValidationStatus.PASSED,
        shopper=passed_shopper,
        garment=passed_garment,
    )

    class MockValidatorService:
        async def validate_and_record(self, **kwargs: object) -> CombinedValidationResult:
            return comb_result

    uc = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,  # type: ignore[arg-type]
        profile_uow=profile_uow,  # type: ignore[arg-type]
        catalog_uow=FakeCatalogUoW(),  # type: ignore[arg-type]
        adapter=adapter,
        validation_service=MockValidatorService(),
    )

    dummy_jpeg = make_dummy_jpeg()
    res = await uc.execute(
        job_id=job_id,
        user_photo_bytes=dummy_jpeg,
        garment_image_bytes=dummy_jpeg,
    )

    assert res.status == "cancelled"
    assert res.failure_reason == "consent_revoked"
    # CRITICAL: Provider adapter submit must NOT have been called!
    assert adapter.submit_called is False
    assert tryon_uow.jobs.cancelled_with == "consent_revoked"
