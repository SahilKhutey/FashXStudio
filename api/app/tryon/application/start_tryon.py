import uuid
from dataclasses import dataclass
from typing import Optional
from fashx.infrastructure.queue.queue_port import QueuePort
from api.app.tryon.domain.cache_keys import compute_tryon_cache_key
from api.app.tryon.repositories.tryon_repository import TryOnRepository


@dataclass(frozen=True)
class StartTryOnCommand:
    user_id: uuid.UUID
    canonical_garment_id: uuid.UUID
    user_photo_id: str
    user_photo_hash: str
    garment_version: int
    model_version: str
    pipeline_version: str
    render_config_hash: str


@dataclass(frozen=True)
class StartTryOnResult:
    job_id: uuid.UUID
    status: str
    cache_hit: bool
    result_image_url: Optional[str] = None


class StartTryOnUseCase:
    def __init__(self, repo: TryOnRepository, queue: QueuePort):
        self.repo = repo
        self.queue = queue

    async def execute(self, cmd: StartTryOnCommand) -> StartTryOnResult:
        cache_key = compute_tryon_cache_key(
            photo_version_hash=cmd.user_photo_hash,
            garment_version=cmd.garment_version,
            model_version=cmd.model_version,
            pipeline_version=cmd.pipeline_version,
            render_config_hash=cmd.render_config_hash,
        )

        cached = await self.repo.find_by_cache_key(cache_key)
        if cached and cached.result_image_url:
            return StartTryOnResult(
                job_id=cached.job_id,
                status="completed",
                cache_hit=True,
                result_image_url=cached.result_image_url,
            )

        job = await self.repo.create_job(
            user_id=cmd.user_id,
            canonical_id=cmd.canonical_garment_id,
            user_photo_id=cmd.user_photo_id,
            cache_key=cache_key,
        )

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
