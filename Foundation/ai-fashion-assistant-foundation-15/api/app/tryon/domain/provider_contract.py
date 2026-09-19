from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProviderJob:
    provider_job_id: str


@dataclass(frozen=True, slots=True)
class ProviderResult:
    result_url: str


@dataclass(frozen=True, slots=True)
class ProviderInput:
    job_id: UUID
    profile_photo_url: str
    garment_image_url: str
    model_version: str
    pipeline_version: str
