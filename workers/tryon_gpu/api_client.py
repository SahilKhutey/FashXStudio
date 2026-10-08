from __future__ import annotations

from uuid import UUID
import httpx

from fashx.core.settings import get_settings
from schemas.tryon.worker import TryOnWorkerClaim, TryOnWorkerComplete, TryOnWorkerFailure, TryOnWorkerProgress


class TryOnInternalApiClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.internal_service_token:
            raise RuntimeError("INTERNAL_SERVICE_TOKEN is required for the try-on worker")
        self.base_url = settings.api_base_url.rstrip("/")
        self.headers = {"X-Internal-Service-Token": settings.internal_service_token}
        self.timeout = settings.worker_http_timeout_seconds

    async def claim(self, job_id: UUID) -> TryOnWorkerClaim:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/claim", headers=self.headers)
            response.raise_for_status()
            return TryOnWorkerClaim.model_validate(response.json())

    async def prepare(self, job_id: UUID) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/prepare", headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def provider_started(self, job_id: UUID, provider_job_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/provider",
                headers=self.headers,
                json={"provider_job_id": provider_job_id},
            )
            response.raise_for_status()
            return response.json()

    async def progress(self, job_id: UUID, status: TryOnWorkerProgress) -> None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/progress", headers=self.headers, json=status.model_dump(mode="json"))
            response.raise_for_status()

    async def complete(self, job_id: UUID, payload: TryOnWorkerComplete) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/complete", headers=self.headers, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            return response.json()

    async def fail(self, job_id: UUID, payload: TryOnWorkerFailure) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/v1/tryon/internal/jobs/{job_id}/fail", headers=self.headers, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            return response.json()
