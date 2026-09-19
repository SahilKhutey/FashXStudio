from __future__ import annotations

import asyncio
from uuid import UUID

import httpx

from api.app.core.errors import AppError
from api.app.core.settings import get_settings
from api.app.tryon.ports.providers import TryOnProvider, TryOnProviderResult, TryOnSubmission


class ConfiguredTryOnProvider(TryOnProvider):
    """Runtime VTO adapter selector.

    ``disabled`` remains the safe default. ``http`` targets a commercial-approved
    VTO endpoint supplied through configuration; the application never embeds a
    research model or vendor SDK directly.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings

    def _require_http(self) -> None:
        if not self.settings.tryon_provider:
            raise AppError(code="gpu_provider_not_configured", message="Try-on GPU provider is not configured", status_code=503)
        if self.settings.tryon_provider == "disabled":
            raise AppError(code="gpu_provider_disabled", message="Try-on GPU provider is disabled", status_code=503)
        if self.settings.tryon_provider != "http":
            raise AppError(
                code="tryon_provider_adapter_missing",
                message=f"No production adapter is registered for provider '{self.settings.tryon_provider}'",
                status_code=503,
            )
        if not self.settings.tryon_provider_url:
            raise AppError(code="gpu_provider_not_configured", message="TRYON_PROVIDER_URL is required", status_code=503)

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.settings.tryon_provider_api_key:
            headers["Authorization"] = f"Bearer {self.settings.tryon_provider_api_key}"
        return headers

    async def submit(
        self,
        *,
        job_id: UUID,
        profile_photo_url: str,
        garment_image_url: str,
        model_version: str,
        pipeline_version: str,
    ) -> TryOnSubmission:
        self._require_http()
        payload = {
            "job_id": str(job_id),
            "profile_photo_url": profile_photo_url,
            "garment_image_url": garment_image_url,
            "model_version": model_version,
            "pipeline_version": pipeline_version,
        }
        timeout = httpx.Timeout(self.settings.tryon_provider_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(self.settings.tryon_provider_url.rstrip("/") + "/jobs", json=payload, headers=self._headers())
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise AppError(code="gpu_provider_submit_failed", message=str(exc), status_code=503) from exc
        provider_job_id = response.json().get("provider_job_id")
        if not isinstance(provider_job_id, str) or not provider_job_id:
            raise AppError(code="gpu_provider_invalid_response", message="Provider did not return provider_job_id", status_code=502)
        return TryOnSubmission(provider_job_id=provider_job_id)

    async def wait_for_result(self, *, provider_job_id: str) -> TryOnProviderResult:
        self._require_http()
        timeout = httpx.Timeout(self.settings.tryon_provider_timeout_seconds)
        deadline = asyncio.get_running_loop().time() + self.settings.tryon_provider_max_wait_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            while True:
                try:
                    response = await client.get(
                        self.settings.tryon_provider_url.rstrip("/") + f"/jobs/{provider_job_id}",
                        headers=self._headers(),
                    )
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    raise AppError(code="gpu_provider_poll_failed", message=str(exc), status_code=503) from exc
                body = response.json()
                state = body.get("status")
                if state == "completed":
                    result_url = body.get("result_url")
                    if not isinstance(result_url, str) or not result_url:
                        raise AppError(code="gpu_provider_invalid_result", message="Provider completed without result_url", status_code=502)
                    return TryOnProviderResult(result_url=result_url)
                if state in {"failed", "cancelled"}:
                    raise AppError(code="gpu_provider_execution_failed", message=f"Provider job ended in state '{state}'", status_code=502)
                if asyncio.get_running_loop().time() >= deadline:
                    raise AppError(code="gpu_provider_timeout", message="Timed out waiting for try-on provider", status_code=504)
                await asyncio.sleep(self.settings.tryon_provider_poll_interval_seconds)
