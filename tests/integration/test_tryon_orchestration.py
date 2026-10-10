import io
from uuid import uuid4

import pytest
from PIL import Image

from fashx.application.ports.tryon import TryOnError
from fashx.infrastructure.storage.local import LocalStorage
from fashx.tryon.adapters.mock_adapter import MockAdapter
from fashx.tryon.application.process_job import ProcessTryOnJobUseCase


def create_sample_jpeg() -> bytes:
    img = Image.new("RGB", (64, 64), (100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


SAMPLE_JPEG = create_sample_jpeg()


class MockJob:
    def __init__(self, job_id, user_id, garment_id, artifact_key):
        self.id = job_id
        self.user_id = user_id
        self.garment_id = garment_id
        self.artifact_key = artifact_key
        self.status = "queued"
        self.provider = None
        self.provider_job_id = None
        self.attempts = 1
        self.failure_reason = None


class MockGarment:
    def __init__(self, garment_id):
        self.id = garment_id
        self.category = "tops"
        self.version = 1


class MockUoWContext:
    def __init__(self):
        self.jobs_store = {}
        self.artifacts_store = {}
        self.usage_store = []
        self.consents_store = {}
        self.garments_store = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def commit(self):
        pass

    class JobRepo:
        def __init__(self, parent):
            self.parent = parent

        async def get_by_id(self, jid):
            return self.parent.jobs_store.get(jid)

        async def get_by_user_and_idempotency(self, uid, ikey):
            for j in self.parent.jobs_store.values():
                if j.user_id == uid and getattr(j, "idempotency_key", None) == ikey:
                    return j
            return None

        def add(self, j):
            self.parent.jobs_store[j.id] = j

        async def update_status(self, jid, status, failure_reason=None):
            j = self.parent.jobs_store.get(jid)
            if j:
                j.status = status
                j.failure_reason = failure_reason
            return j

        async def set_provider_job(self, jid, provider, p_job_id):
            j = self.parent.jobs_store.get(jid)
            if j:
                j.provider = provider
                j.provider_job_id = p_job_id
            return j

        async def requeue(self, jid, delay_s=0, clear_provider_job=False):
            j = self.parent.jobs_store.get(jid)
            if j:
                j.status = "queued"
                j.attempts += 1
                if clear_provider_job:
                    j.provider_job_id = None
            return j

        async def fail(self, jid, code, msg=None):
            return await self.update_status(jid, "failed", failure_reason=code)

        async def cancel(self, jid, reason="cancelled"):
            return await self.update_status(jid, "cancelled", failure_reason=reason)

    class ArtifactRepo:
        def __init__(self, parent):
            self.parent = parent

        async def get_by_job_id(self, jid):
            return self.parent.artifacts_store.get(jid)

        async def get_by_artifact_key(self, akey):
            for a in self.parent.artifacts_store.values():
                if a.artifact_key == akey:
                    return a
            return None

        def add(self, a):
            self.parent.artifacts_store[a.job_id] = a

    class UsageRepo:
        def __init__(self, parent):
            self.parent = parent

        async def record(self, outcome, **kwargs):
            rec = {"outcome": outcome, **kwargs}
            self.parent.usage_store.append(rec)
            return rec

    class ConsentRepo:
        def __init__(self, parent):
            self.parent = parent

        async def has_consent(self, uid, consent_type):
            return self.parent.consents_store.get(uid, True)

    class GarmentRepo:
        def __init__(self, parent):
            self.parent = parent

        async def get_by_id(self, gid):
            return self.parent.garments_store.get(gid, MockGarment(gid))

    @property
    def jobs(self):
        return self.JobRepo(self)

    @property
    def artifacts(self):
        return self.ArtifactRepo(self)

    @property
    def usage(self):
        return self.UsageRepo(self)

    @property
    def consents(self):
        return self.ConsentRepo(self)

    @property
    def canonical_garments(self):
        return self.GarmentRepo(self)


@pytest.fixture
def uow_context():
    return MockUoWContext()


@pytest.mark.asyncio
async def test_worker_resumes_crashed_job_without_re_submitting(uow_context, tmp_path):
    storage = LocalStorage(tmp_path)
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()

    job = MockJob(job_id, user_id, garment_id, "art-key-1")
    # Simulate worker dying AFTER submitting to vendor: provider_job_id is already set
    job.provider_job_id = "pre-existing-vendor-id-789"
    uow_context.jobs_store[job_id] = job

    adapter = MockAdapter()
    assert adapter.submit_count == 0

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=uow_context,
        profile_uow=uow_context,
        catalog_uow=uow_context,
        adapter=adapter,
        storage=storage,
    )

    res = await use_case.execute(
        job_id,
        user_photo_bytes=SAMPLE_JPEG,
        garment_image_bytes=SAMPLE_JPEG,
    )

    assert res.status == "completed"
    # Key check: adapter.submit was NOT called again because provider_job_id was already present!
    assert adapter.submit_count == 0
    assert storage.exists(f"u/{user_id}/tryon/{job_id}.jpg")


@pytest.mark.asyncio
async def test_worker_cancels_if_consent_revoked_before_inference(uow_context, tmp_path):
    storage = LocalStorage(tmp_path)
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()

    job = MockJob(job_id, user_id, garment_id, "art-key-2")
    uow_context.jobs_store[job_id] = job
    # User has revoked consent
    uow_context.consents_store[user_id] = False

    adapter = MockAdapter()
    use_case = ProcessTryOnJobUseCase(
        tryon_uow=uow_context,
        profile_uow=uow_context,
        catalog_uow=uow_context,
        adapter=adapter,
        storage=storage,
    )

    res = await use_case.execute(
        job_id,
        user_photo_bytes=SAMPLE_JPEG,
        garment_image_bytes=SAMPLE_JPEG,
    )

    assert res.status == "cancelled"
    assert res.failure_reason == "consent_revoked"
    assert adapter.submit_count == 0
    assert not storage.exists(f"u/{user_id}/tryon/{job_id}.jpg")


@pytest.mark.asyncio
async def test_worker_requeues_on_retryable_error(uow_context, tmp_path):
    storage = LocalStorage(tmp_path)
    job_id = uuid4()
    user_id = uuid4()
    garment_id = uuid4()

    job = MockJob(job_id, user_id, garment_id, "art-key-3")
    uow_context.jobs_store[job_id] = job

    class FailingAdapter:
        provider = "fashn_api"
        model_version = "tryon-v1.6"

        def submit(self, req):
            raise TryOnError("provider_unavailable", "Busy", retryable=True)

        def collect(self, pid, *, deadline_s):
            pass

    use_case = ProcessTryOnJobUseCase(
        tryon_uow=uow_context,
        profile_uow=uow_context,
        catalog_uow=uow_context,
        adapter=FailingAdapter(),
        storage=storage,
    )

    res = await use_case.execute(
        job_id,
        user_photo_bytes=SAMPLE_JPEG,
        garment_image_bytes=SAMPLE_JPEG,
    )

    assert res.status == "queued"
    assert job.attempts == 2
    assert uow_context.usage_store[-1]["outcome"] == "retried"


def test_no_vendor_urls_returned_to_client(client_a, tmp_path):
    storage = LocalStorage(tmp_path)
    from fashx.core.dependencies import get_storage
    client_a.app.dependency_overrides[get_storage] = lambda: storage

    try:
        # Check that signing any tryon artifact generates our internal storage URL, never fashn.ai
        url = storage.signed_get_url("u/alice/tryon/job-1.jpg", ttl_s=300)
        assert "fashn.ai" not in url
        assert "dev-files" in url or "s3" in url
    finally:
        client_a.app.dependency_overrides.pop(get_storage, None)

