"""
Start Try-On Use Case (Rule I02)
Orchestrates capability verification, domain artifact key hashing,
cache lookup, repository persistence, and queue dispatch.
"""

import uuid
from dataclasses import dataclass
from typing import Optional
from app.application.ports.queue_port import JobQueuePort
from app.domain.tryon_keys import compute_tryon_artifact_key
from app.repositories.tryon_repo import TryOnRepository


@dataclass(frozen=True)
class StartTryOnCommand:
    user_id: uuid.UUID
    canonical_garment_id: uuid.UUID
    user_photo_id: str
    user_photo_hash: str
    canonical_garment_version: int
    model_adapter_id: str
    model_weights_version: str
    preprocessing_version: str
    render_config_hash: str


@dataclass(frozen=True)
class StartTryOnResult:
    job_id: uuid.UUID
    status: str
    cache_hit: bool
    result_image_url: Optional[str] = None


class StartTryOnUseCase:
    def __init__(
        self,
        tryon_repo: TryOnRepository,
        queue: JobQueuePort,
    ):
        self.tryon_repo = tryon_repo
        self.queue = queue

    async def execute(self, cmd: StartTryOnCommand) -> StartTryOnResult:
        # 1. Domain logic: compute deterministic artifact key
        cache_key = compute_tryon_artifact_key(
            user_photo_version_hash=cmd.user_photo_hash,
            canonical_garment_version=cmd.canonical_garment_version,
            model_adapter_id=cmd.model_adapter_id,
            model_weights_version=cmd.model_weights_version,
            preprocessing_version=cmd.preprocessing_version,
            render_config_hash=cmd.render_config_hash,
        )

        # 2. Check repository for valid cached artifact
        cached_job = await self.tryon_repo.find_successful_by_cache_key(cache_key)
        if cached_job and cached_job.result_image_url:
            return StartTryOnResult(
                job_id=cached_job.job_id,
                status="completed",
                cache_hit=True,
                result_image_url=cached_job.result_image_url,
            )

        # 3. Create new queued job record
        job = await self.tryon_repo.create_job(
            user_id=cmd.user_id,
            canonical_id=cmd.canonical_garment_id,
            user_photo_id=cmd.user_photo_id,
            cache_key=cache_key,
        )

        # 4. Enqueue background task
        await self.queue.enqueue(
            queue_name="vto_diffusion_jobs",
            payload={
                "job_id": str(job.job_id),
                "user_id": str(cmd.user_id),
                "canonical_id": str(cmd.canonical_garment_id),
                "cache_key": cache_key,
            },
            job_id=str(job.job_id),
        )

        return StartTryOnResult(
            job_id=job.job_id,
            status="queued",
            cache_hit=False,
            result_image_url=None,
        )
