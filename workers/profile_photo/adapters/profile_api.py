from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from fashx.core.settings import get_settings


class ProfilePhotoApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        token = self.settings.internal_service_token
        if not token:
            raise RuntimeError("INTERNAL_SERVICE_TOKEN is required for worker callbacks")
        return {"X-Internal-Service-Token": token}

    async def claim_job(self, job_id: UUID) -> dict[str, Any]:
        url = f"{self.settings.api_base_url}/api/v1/profile/internal/photo-jobs/{job_id}/claim"
        async with httpx.AsyncClient(timeout=self.settings.worker_http_timeout_seconds) as client:
            response = await client.post(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def complete_job(self, job_id: UUID, *, result: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.api_base_url}/api/v1/profile/internal/photo-jobs/{job_id}/complete"
        async with httpx.AsyncClient(timeout=self.settings.worker_http_timeout_seconds) as client:
            response = await client.post(url, headers=self._headers(), json=result)
            response.raise_for_status()
            return response.json()

    async def fail_job(self, job_id: UUID, *, reason: str, retryable: bool) -> dict[str, Any]:
        url = f"{self.settings.api_base_url}/api/v1/profile/internal/photo-jobs/{job_id}/fail"
        async with httpx.AsyncClient(timeout=self.settings.worker_http_timeout_seconds) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={"reason": reason, "retryable": retryable},
            )
            response.raise_for_status()
            return response.json()
