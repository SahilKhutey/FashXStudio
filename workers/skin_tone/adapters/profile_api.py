from __future__ import annotations

from typing import Any
from uuid import UUID
import httpx

from fashx.core.settings import get_settings


class ProfileIntelligenceApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        token = self.settings.internal_service_token
        if not token:
            raise RuntimeError("INTERNAL_SERVICE_TOKEN is required")
        return {"X-Internal-Service-Token": token}

    async def media_url(self, photo_id: UUID, job_id: UUID, purpose: str) -> str:
        url = f"{self.settings.api_base_url}/api/v1/profile/internal/media-access"
        async with httpx.AsyncClient(timeout=self.settings.worker_http_timeout_seconds) as client:
            response = await client.post(url, headers=self._headers(), json={"photo_id": str(photo_id), "job_id": str(job_id), "purpose": purpose})
            response.raise_for_status()
            return response.json()["access_url"]

    async def write_result(self, job_id: UUID, result: dict[str, Any]) -> None:
        url = f"{self.settings.api_base_url}/api/v1/profile/internal/skin-tone-jobs/{job_id}/complete"
        async with httpx.AsyncClient(timeout=self.settings.worker_http_timeout_seconds) as client:
            response = await client.post(url, headers=self._headers(), json=result)
            response.raise_for_status()
