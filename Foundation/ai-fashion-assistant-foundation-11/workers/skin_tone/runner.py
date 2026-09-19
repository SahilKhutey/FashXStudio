from __future__ import annotations

import asyncio
import io
import json
import logging
from typing import Any
from uuid import UUID

import httpx
import numpy as np
from PIL import Image

from api.app.core.settings import get_settings
from workers.profile_photo.adapters.storage import ObjectStorageDownloadPort
from api.app.profile.integrations.r2_client import R2StorageClient
from workers.skin_tone.adapters.profile_api import ProfileIntelligenceApiClient
from workers.skin_tone.domain.ita import estimate_ita

logger = logging.getLogger(__name__)
QUEUE_NAME = "skin-tone-processing"


class SkinToneWorker:
    def __init__(self, *, queue_client: Any | None = None, storage: ObjectStorageDownloadPort | None = None, profile_api: ProfileIntelligenceApiClient | None = None) -> None:
        settings = get_settings()
        if queue_client is not None:
            self.redis = queue_client
        else:
            import redis.asyncio as redis
            self.redis = redis.from_url(settings.redis_url, decode_responses=True)
        self.storage = storage or R2StorageClient()
        self.profile_api = profile_api or ProfileIntelligenceApiClient()

    async def process_message(self, message: dict[str, Any]) -> bool:
        job_id = UUID(message["job_id"])
        photo_id = UUID(message["photo_id"])
        access_url = await self.profile_api.media_url(photo_id, job_id, "skin_tone")
        try:
            async with httpx.AsyncClient(timeout=get_settings().worker_http_timeout_seconds) as client:
                response = await client.get(access_url)
                response.raise_for_status()
                payload = response.content
            image = Image.open(io.BytesIO(payload)).convert("RGB")
            image_bgr = cv2_from_pil(image)
            result = estimate_ita(image_bgr)
            await self.profile_api.write_result(job_id, {
                "status": "completed" if result.ita_degrees is not None else "failed",
                "ita_degrees": result.ita_degrees,
                "tone_class": result.tone_class,
                "confidence": result.confidence,
                "method": result.method,
                "model_version": result.model_version,
                "photo_id": str(photo_id),
                "user_id": message["user_id"],
            })
            return True
        except (TimeoutError, ConnectionError, httpx.HTTPError) as exc:
            logger.warning("skin_tone_retryable_failure", extra={"job_id": str(job_id), "error": str(exc)})
            return False

    async def run_forever(self) -> None:
        logger.info("skin_tone_worker_started", extra={"queue": QUEUE_NAME})
        while True:
            result = await self.redis.blpop(QUEUE_NAME, timeout=30)
            if result is None:
                continue
            _, raw = result
            await self.process_message(json.loads(raw))

    async def close(self) -> None:
        await self.redis.aclose()


def cv2_from_pil(image: Image.Image):
    import cv2
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


async def main() -> None:
    worker = SkinToneWorker()
    try:
        await worker.run_forever()
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
