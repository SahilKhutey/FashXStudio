from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TryOnSubmission:
    provider_job_id: str


@dataclass(frozen=True, slots=True)
class TryOnProviderResult:
    result_url: str


class TryOnProvider(Protocol):
    async def submit(
        self,
        *,
        job_id: UUID,
        profile_photo_url: str,
        garment_image_url: str,
        model_version: str,
        pipeline_version: str,
    ) -> TryOnSubmission: ...

    async def wait_for_result(self, *, provider_job_id: str) -> TryOnProviderResult: ...


class TryOnProfilePort(Protocol):
    async def get_accepted_photo(self, *, user_id: UUID, photo_id: UUID) -> dict: ...


class TryOnCatalogPort(Protocol):
    async def get_garment_for_tryon(self, *, garment_id: UUID) -> dict: ...
