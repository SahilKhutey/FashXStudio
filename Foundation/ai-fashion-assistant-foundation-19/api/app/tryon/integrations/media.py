from __future__ import annotations

from asyncio import to_thread

import httpx

from api.app.core.settings import get_settings
from api.app.profile.integrations.r2_client import R2StorageClient
from api.app.tryon.domain.result_quality import ResultQuality, validate_result_bytes
from api.app.tryon.ports.providers import TryOnProvider, TryOnProviderResult, TryOnSubmission


class ResultQualityError(RuntimeError):
    """Raised when a provider result cannot be safely accepted."""


class TryOnExecutionGateway:
    def __init__(self, *, storage: R2StorageClient, provider: TryOnProvider) -> None:
        self.storage = storage
        self.provider = provider
        self.settings = get_settings()

    async def submit(self, *, job_id, photo_key, garment_key, model_version, pipeline_version) -> TryOnSubmission:
        photo_url, _ = await to_thread(self.storage.create_download_url, key=photo_key, expires_in=self.settings.tryon_input_url_ttl_seconds)
        garment_url, _ = await to_thread(self.storage.create_download_url, key=garment_key, expires_in=self.settings.tryon_input_url_ttl_seconds)
        return await self.provider.submit(
            job_id=job_id,
            profile_photo_url=photo_url,
            garment_image_url=garment_url,
            model_version=model_version,
            pipeline_version=pipeline_version,
        )

    async def fetch_result_to_r2(self, *, provider_result: TryOnProviderResult, result_key: str) -> tuple[str, ResultQuality]:
        timeout = httpx.Timeout(self.settings.tryon_provider_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                response = await client.get(provider_result.result_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"Unable to download provider result: {exc}") from exc
        quality = validate_result_bytes(
            response.content,
            declared_content_type=response.headers.get("content-type"),
            min_width=self.settings.tryon_result_min_width,
            min_height=self.settings.tryon_result_min_height,
            max_bytes=self.settings.tryon_result_max_bytes,
        )
        if not quality.accepted or quality.quality_score < self.settings.tryon_result_quality_threshold:
            raise ResultQualityError("Try-on result failed quality validation: " + ",".join(quality.reasons or ("quality_score_below_threshold",)))
        await to_thread(self.storage.upload_bytes, key=result_key, content=response.content, content_type=quality.content_type)
        return result_key, quality
