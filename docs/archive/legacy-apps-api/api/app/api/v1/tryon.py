"""
Try-On Router (Rule I01)
HTTP routing only. Delegates execution to StartTryOnUseCase.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.use_cases.start_tryon import StartTryOnCommand, StartTryOnUseCase
from app.config.base import get_settings
from app.infrastructure.database.session import get_db_session
from app.infrastructure.queue.local_queue import LocalJobQueueAdapter
from app.repositories.tryon_repo import TryOnRepository

router = APIRouter(prefix="/try-on", tags=["Virtual Try-On"])

# Shared singleton queue adapter for modular monolith
local_queue_singleton = LocalJobQueueAdapter()


class StartTryOnRequest(BaseModel):
    canonical_garment_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    user_photo_id: str
    user_photo_hash: str
    canonical_garment_version: int = 1
    render_config_hash: str = "default_1024x768"


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_try_on(
    request: StartTryOnRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_session),
):
    settings = get_settings()

    # Rule I01: Router creates repository and passes to application use case
    repo = TryOnRepository(db)
    use_case = StartTryOnUseCase(tryon_repo=repo, queue=local_queue_singleton)

    # In production, user_id is extracted from authenticated JWT bearer token
    mock_user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

    cmd = StartTryOnCommand(
        user_id=mock_user_id,
        canonical_garment_id=request.canonical_garment_id,
        user_photo_id=request.user_photo_id,
        user_photo_hash=request.user_photo_hash,
        canonical_garment_version=request.canonical_garment_version,
        model_adapter_id=settings.ACTIVE_TRYON_MODEL,
        model_weights_version=settings.ACTIVE_TRYON_MODEL_WEIGHTS,
        preprocessing_version=settings.TRYON_PREPROCESSING_VERSION,
        render_config_hash=request.render_config_hash,
    )

    result = await use_case.execute(cmd)

    if result.cache_hit:
        return {
            "job_id": str(result.job_id),
            "status": "completed",
            "cache_hit": True,
            "result_image_url": result.result_image_url,
        }

    return {
        "job_id": str(result.job_id),
        "status": "queued",
        "cache_hit": False,
        "estimated_wait_seconds": 4,
        "poll_url": f"/api/v1/try-on/{result.job_id}",
    }


@router.get("/{job_id}", status_code=status.HTTP_200_OK)
async def get_try_on_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    repo = TryOnRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Try-on job {job_id} not found",
        )

    return {
        "job_id": str(job.job_id),
        "status": job.status,
        "result_image_url": job.result_image_url,
        "error_code": job.error_code,
        "error_message": job.error_message,
        "completed_at": job.completed_at,
    }
