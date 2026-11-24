"""Unit tests for worker provider attempt tracking, output validation, and recovery (Phase 07.4)."""

from __future__ import annotations

import io
from types import SimpleNamespace
from uuid import uuid4

from PIL import Image

from fashx.tryon.application.process_job import ProcessTryOnJobUseCase


def make_test_jpeg(size: tuple[int, int] = (600, 800), color: str = "blue") -> bytes:
    from PIL import ImageDraw

    im = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(im)
    draw.rectangle([100, 100, 400, 400], fill="white")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    return buf.getvalue()


class FakeProviderAttemptRepo:
    def __init__(self) -> None:
        self.attempts: list[object] = []

    async def get_by_job_id(self, job_id: object) -> list[object]:
        return [a for a in self.attempts if a.job_id == job_id]

    async def create_attempt(self, **kwargs: object) -> object:
        att = SimpleNamespace(
            id=uuid4(),
            job_id=kwargs.get("job_id"),
            attempt_number=kwargs.get("attempt_number"),
            provider=kwargs.get("provider"),
            model_version=kwargs.get("model_version"),
            status=kwargs.get("status"),
            request_hash=kwargs.get("request_hash"),
            provider_job_id=kwargs.get("provider_job_id"),
            submitted_at=None,
            completed_at=None,
        )
        self.attempts.append(att)
        return att

    async def update_status(self, attempt_id: object, status: str, **kwargs: object) -> object | None:
        for a in self.attempts:
            if a.id == attempt_id:
                a.status = status
                for k, v in kwargs.items():
                    setattr(a, k, v)
                return a
        return None


class FakeJobRepo:
    def __init__(self, job: object) -> None:
        self.job = job

    async def get_by_id(self, jid: object) -> object | None:
        return self.job if self.job and self.job.id == jid else None

    async def update_status(self, job_id: object, status: str, failure_reason: str | None = None) -> object:
        self.job.status = status
        self.job.failure_reason = failure_reason
        return self.job

    async def set_provider_job(self, job_id: object, provider: str, prov_id: str) -> object:
        self.job.provider = provider
        self.job.provider_job_id = prov_id
        return self.job

    async def cancel(self, job_id: object, reason: str) -> object:
        self.job.status = "cancelled"
        self.job.failure_reason = reason
        return self.job

    async def fail(self, job_id: object, error_code: str, user_message: str | None = None) -> object:
        self.job.status = "failed"
        self.job.failure_reason = error_code
        return self.job


class FakeArtifactRepo:
    def __init__(self) -> None:
        self.created: list[object] = []

    def add(self, artifact: object) -> None:
        self.created.append(artifact)

    async def get_by_job_id(self, jid: object) -> object | None:
        for a in self.created:
            if getattr(a, "job_id", None) == jid:
                return a
        return None


class FakeUsageRepo:
    def __init__(self) -> None:
        self.records: list[dict] = []

    async def record(self, outcome: str, **kwargs: object) -> None:
        self.records.append({"outcome": outcome, **kwargs})


class FakeTryOnUoW:
    def __init__(self, job: object) -> None:
        self.jobs = FakeJobRepo(job)
        self.provider_attempts = FakeProviderAttemptRepo()
        self.artifacts = FakeArtifactRepo()
        self.usage = FakeUsageRepo()

    async def __aenter__(self) -> FakeTryOnUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def commit(self) -> None:
        pass


class FakeProfileUoW:
    def __init__(self, user_id: object) -> None:
        async def fake_has_consent(uid: object, purpose: str) -> bool:
            return True

        self.consents = SimpleNamespace(has_consent=fake_has_consent)
        self.photos = SimpleNamespace(
            get_by_id=lambda pid: SimpleNamespace(id=pid, storage_key="u/photo.jpg", status="accepted")
        )

    async def __aenter__(self) -> FakeProfileUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


class FakeCatalogUoW:
    def __init__(self, garment_id: object) -> None:
        async def fake_get_garment(gid: object) -> object:
            return SimpleNamespace(
                id=gid, category="tops", version=1, status="ACTIVE", tryon_supported=True
            )

        self.canonical_garments = SimpleNamespace(get_by_id=fake_get_garment)
        self.garment_images = SimpleNamespace(
            get_by_id=lambda iid: SimpleNamespace(id=iid, storage_key="g/img.jpg")
        )

    async def __aenter__(self) -> FakeCatalogUoW:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def get(self, key: str) -> bytes:
        return self.objects.get(key, make_test_jpeg())

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        self.objects[key] = data

    def exists(self, key: str) -> bool:
        return key in self.objects

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


async def test_worker_submission_timeout_moves_to_submission_unknown() -> None:
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        garment_id=garment_id,
        profile_photo_id=uuid4(),
        status="queued",
        artifact_key="art-key-1",
        request_hash="req-hash-1",
        provider=None,
        provider_job_id=None,
        cancel_requested=False,
        progress_stage=None,
        attempts=1,
    )

    tryon_uow = FakeTryOnUoW(job)
    profile_uow = FakeProfileUoW(user_id)
    catalog_uow = FakeCatalogUoW(garment_id)
    storage = FakeStorage()

    class TimeoutAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "v1"

        def submit(self, req: object) -> str:
            raise TimeoutError("Connection to provider timed out")

        def collect(self, pid: str, **kwargs: object) -> object:
            raise NotImplementedError()

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=TimeoutAdapter(),
        storage=storage,
    )

    valid_jpeg = make_test_jpeg()
    res = await use_case.execute(job_id, user_photo_bytes=valid_jpeg, garment_image_bytes=valid_jpeg)

    assert res.status == "submission_unknown"
    assert job.status == "submission_unknown"
    assert job.progress_stage == "submission_unknown"
    # Verify attempt record was saved with status UNKNOWN
    attempts = await tryon_uow.provider_attempts.get_by_job_id(job_id)
    assert len(attempts) == 1
    assert attempts[0].status == "UNKNOWN"


async def test_worker_successful_submission_and_completion() -> None:
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        garment_id=garment_id,
        profile_photo_id=uuid4(),
        status="queued",
        artifact_key="art-key-2",
        request_hash="req-hash-2",
        provider=None,
        provider_job_id=None,
        cancel_requested=False,
        progress_stage=None,
        attempts=1,
    )

    tryon_uow = FakeTryOnUoW(job)
    profile_uow = FakeProfileUoW(user_id)
    catalog_uow = FakeCatalogUoW(garment_id)
    storage = FakeStorage()

    class SuccessAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "v1"

        def submit(self, req: object) -> str:
            return "prov-job-999"

        def collect(self, pid: str, **kwargs: object) -> object:
            return SimpleNamespace(
                image_bytes=make_test_jpeg(),
                latency_ms=1200,
                cost_usd_est=0.075,
                model="tryon-v1.6",
                provider="fashn_api",
            )

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=SuccessAdapter(),
        storage=storage,
    )

    valid_jpeg = make_test_jpeg()
    res = await use_case.execute(job_id, user_photo_bytes=valid_jpeg, garment_image_bytes=valid_jpeg)

    assert res.status == "completed"
    assert job.status == "completed"
    assert job.provider_job_id == "prov-job-999"
    # Verify attempt was recorded as COMPLETED
    attempts = await tryon_uow.provider_attempts.get_by_job_id(job_id)
    assert len(attempts) == 1
    assert attempts[0].status == "COMPLETED"
    assert attempts[0].provider_job_id == "prov-job-999"

    # Verify artifact created
    assert len(tryon_uow.artifacts.created) == 1
    art = tryon_uow.artifacts.created[0]
    assert art.provider == "fashn_api"
    assert art.processing_latency_ms == 1200
    assert art.quality_status == "accepted"


async def test_worker_output_validation_rejects_corrupted_output() -> None:
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        garment_id=garment_id,
        profile_photo_id=uuid4(),
        status="queued",
        artifact_key="art-key-3",
        request_hash="req-hash-3",
        provider=None,
        provider_job_id=None,
        cancel_requested=False,
        progress_stage=None,
        attempts=1,
    )

    tryon_uow = FakeTryOnUoW(job)
    profile_uow = FakeProfileUoW(user_id)
    catalog_uow = FakeCatalogUoW(garment_id)
    storage = FakeStorage()

    class CorruptAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"
        pipeline_version = "v1"

        def submit(self, req: object) -> str:
            return "prov-job-corrupt"

        def collect(self, pid: str, **kwargs: object) -> object:
            # Return corrupt non-image bytes
            return SimpleNamespace(
                image_bytes=b"corrupted-non-image-data-payload",
                latency_ms=500,
                cost_usd_est=0.075,
                model="tryon-v1.6",
                provider="fashn_api",
            )

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        adapter=CorruptAdapter(),
        storage=storage,
    )

    valid_jpeg = make_test_jpeg()
    res = await use_case.execute(job_id, user_photo_bytes=valid_jpeg, garment_image_bytes=valid_jpeg)

    assert res.status == "failed"
    assert job.status == "failed"
    assert job.failure_reason == "output_validation_failed"
    # Ensure no artifact was persisted
    assert len(tryon_uow.artifacts.created) == 0
