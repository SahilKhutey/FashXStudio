from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from workers.profile_photo.domain.processing import ProcessedPhoto
from workers.profile_photo.domain.validation import PhotoValidationResult
from workers.profile_photo.runner import ProfilePhotoWorker


@dataclass
class FakeStorage:
    payload: bytes

    def download_bytes(self, *, key: str) -> bytes:
        assert key == "user-photos/x/photo.jpg"
        return self.payload


class FakeProfileApi:
    def __init__(self) -> None:
        self.calls = []

    async def claim_job(self, job_id):
        self.calls.append(("claim", job_id))
        return {
            "claimed": True,
            "job_id": job_id,
            "photo_id": uuid4(),
            "user_id": uuid4(),
            "photo_type": "tryon_reference",
            "storage_key": "user-photos/x/photo.jpg",
            "attempt_count": 1,
        }

    async def complete_job(self, job_id, *, result):
        self.calls.append(("complete", job_id, result))
        return {"status": "completed"}

    async def fail_job(self, job_id, *, reason, retryable):
        self.calls.append(("fail", job_id, reason, retryable))
        return {"status": "failed"}


class FakeProcessor:
    def __init__(self, accepted: bool) -> None:
        self.accepted = accepted

    def process(self, payload: bytes, *, photo_type: str) -> ProcessedPhoto:
        return ProcessedPhoto(
            PhotoValidationResult(
                accepted=self.accepted,
                reason=None if self.accepted else "person_not_detected",
                content_sha256="a" * 64,
                width=640,
                height=960,
                image_format="jpeg",
                mode="RGB",
                has_person=self.accepted,
                has_face=False,
            )
        )


class FakeRedis:
    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_worker_completes_accepted_job() -> None:
    profile_api = FakeProfileApi()
    worker = ProfilePhotoWorker(
        queue_client=FakeRedis(),
        storage=FakeStorage(b"payload"),
        profile_api=profile_api,
        processor=FakeProcessor(True),
    )
    job_id = uuid4()
    assert await worker.process_message({"job_id": str(job_id)}) is True
    assert profile_api.calls[0][0] == "claim"
    assert profile_api.calls[1][0] == "complete"
    assert profile_api.calls[1][2]["file_size_bytes"] == len(b"payload")


@pytest.mark.asyncio
async def test_worker_rejects_invalid_photo_without_retry() -> None:
    profile_api = FakeProfileApi()
    worker = ProfilePhotoWorker(
        queue_client=FakeRedis(),
        storage=FakeStorage(b"payload"),
        profile_api=profile_api,
        processor=FakeProcessor(False),
    )
    assert await worker.process_message({"job_id": str(uuid4())}) is True
    assert profile_api.calls[-1][0] == "fail"
    assert profile_api.calls[-1][3] is False


@pytest.mark.asyncio
async def test_worker_skips_unclaimed_job() -> None:
    class SkipApi(FakeProfileApi):
        async def claim_job(self, job_id):
            return {"claimed": False, "reason": "already_claimed_or_terminal"}

    profile_api = SkipApi()
    worker = ProfilePhotoWorker(
        queue_client=FakeRedis(),
        storage=FakeStorage(b"payload"),
        profile_api=profile_api,
        processor=FakeProcessor(True),
    )
    assert await worker.process_message({"job_id": str(uuid4())}) is True
    assert len(profile_api.calls) == 0
