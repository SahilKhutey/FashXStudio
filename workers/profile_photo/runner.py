from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from api.app.core.settings import get_settings
from workers.profile_photo.adapters.profile_api import ProfilePhotoApiClient
from workers.profile_photo.domain.processing import ProfilePhotoProcessor
from workers.profile_photo.adapters.storage import ObjectStorageDownloadPort
from fashx.profile.integrations.r2_client import R2StorageClient

logger = logging.getLogger(__name__)

QUEUE_NAME = "profile-photo-processing"


class ProfilePhotoWorker:
    def __init__(
        self,
        *,
        queue_client: Any | None = None,
        storage: ObjectStorageDownloadPort | None = None,
        profile_api: ProfilePhotoApiClient | None = None,
        processor: ProfilePhotoProcessor | None = None,
    ) -> None:
        settings = get_settings()
        if queue_client is not None:
            self.redis = queue_client
        else:
            import redis.asyncio as redis
            self.redis = redis.from_url(settings.redis_url, decode_responses=True)
        self.storage = storage or R2StorageClient()
        self.profile_api = profile_api or ProfilePhotoApiClient()
        self.processor = processor or ProfilePhotoProcessor()
        self.settings = settings

    async def process_message(self, message: dict[str, Any]) -> bool:
        job_id = UUID(message["job_id"])
        claimed = await self.profile_api.claim_job(job_id)
        if not claimed.get("claimed", False):
            logger.info("profile_photo_job_skipped", extra={"job_id": str(job_id), "reason": claimed.get("reason")})
            return True

        photo_type = claimed["photo_type"]
        storage_key = claimed["storage_key"]
        try:
            payload = await asyncio.to_thread(self.storage.download_bytes, key=storage_key)
            if len(payload) > self.settings.profile_photo_max_bytes:
                await self.profile_api.fail_job(job_id, reason="file_too_large", retryable=False)
                return True
            processed = await asyncio.to_thread(self.processor.process, payload, photo_type=photo_type)
            result = processed.result
            if not result.accepted:
                await self.profile_api.fail_job(job_id, reason=result.reason or "validation_failed", retryable=False)
                return True

            await self.profile_api.complete_job(
                job_id,
                result={
                    "content_sha256": result.content_sha256,
                    "width": result.width,
                    "height": result.height,
                    "image_format": result.image_format,
                    "mode": result.mode,
                    "has_person": result.has_person,
                    "has_face": result.has_face,
                    "file_size_bytes": len(payload),
                    "quality_score": result.capture_quality.score if result.capture_quality else None,
                    "pose_score": result.capture_quality.pose_score if result.capture_quality else None,
                    "framing_score": result.capture_quality.framing_score if result.capture_quality else None,
                    "landmark_confidence": result.capture_quality.landmark_confidence if result.capture_quality else None,
                    "ready_for_tryon": result.capture_quality.ready_for_tryon if result.capture_quality else None,
                    "quality_reasons": list(result.capture_quality.reasons) if result.capture_quality else [],
                    "pose_provider": result.pose_estimate.provider if result.pose_estimate else None,
                    "pose_provider_version": result.pose_estimate.provider_version if result.pose_estimate else None,
                },
            )
            return True
        except (TimeoutError, ConnectionError) as exc:
            logger.warning("profile_photo_job_retryable_failure", extra={"job_id": str(job_id), "error": str(exc)})
            await self.profile_api.fail_job(job_id, reason="transient_dependency_error", retryable=True)
            return False
        except Exception:
            logger.exception("profile_photo_job_failed", extra={"job_id": str(job_id)})
            await self.profile_api.fail_job(job_id, reason="internal_error", retryable=False)
            return True

    async def run_forever(self) -> None:
        logger.info("profile_photo_worker_started", extra={"queue": QUEUE_NAME})
        while True:
            result = await self.redis.blpop(QUEUE_NAME, timeout=30)
            if result is None:
                continue
            _, raw = result
            message = json.loads(raw)
            await self.process_message(message)

    async def close(self) -> None:
        await self.redis.aclose()


async def main() -> None:
    worker = ProfilePhotoWorker()
    try:
        await worker.run_forever()
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
