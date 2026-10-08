from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.auth.internal import require_internal_service
from api.app.core.dependencies import catalog_repository, db_session, profile_media_repository
from api.app.profile.repositories.media import ProfileMediaRepository
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.profile.integrations.r2_client import R2StorageClient
from api.app.profile.integrations.redis_queue import RedisQueue
from api.app.tryon.application.service import TryOnApplicationService
from api.app.tryon.integrations.catalog_client import LocalCatalogTryOnClient
from api.app.tryon.integrations.profile_client import LocalProfileTryOnClient
from api.app.tryon.repositories.tryon import TryOnRepository
from schemas.tryon.job import TryOnCancelResponse, TryOnCreate, TryOnCreateResponse, TryOnStatusResponse
from schemas.tryon.worker import TryOnWorkerClaim, TryOnWorkerComplete, TryOnWorkerFailure, TryOnWorkerProgress
from schemas.tryon.result import TryOnResultMetadata

router = APIRouter(prefix="/api/v1/tryon", tags=["try-on"])


def get_service(
    session: AsyncSession = Depends(db_session),
    catalog: CatalogRepository = Depends(catalog_repository),
    profile: ProfileMediaRepository = Depends(profile_media_repository),
) -> TryOnApplicationService:
    return TryOnApplicationService(
        repository=TryOnRepository(session),
        profile=LocalProfileTryOnClient(profile),
        catalog=LocalCatalogTryOnClient(catalog),
        queue=RedisQueue(),
        storage=R2StorageClient(),
    )


@router.post("", response_model=TryOnCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_tryon(
    request: Request,
    payload: TryOnCreate,
    user_id: UUID = Depends(current_user_id),
    service: TryOnApplicationService = Depends(get_service),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> TryOnCreateResponse:
    if not idempotency_key:
        from api.app.core.errors import ConflictError
        raise ConflictError("Idempotency-Key header is required for try-on requests")
    return await service.create(user_id=user_id, request=payload, idempotency_key=idempotency_key)


@router.get("/{job_id}", response_model=TryOnStatusResponse)
async def get_tryon_status(
    job_id: UUID,
    user_id: UUID = Depends(current_user_id),
    service: TryOnApplicationService = Depends(get_service),
) -> TryOnStatusResponse:
    return await service.get_status(user_id=user_id, job_id=job_id)


@router.post("/{job_id}/cancel", response_model=TryOnCancelResponse)
async def cancel_tryon(
    job_id: UUID,
    user_id: UUID = Depends(current_user_id),
    service: TryOnApplicationService = Depends(get_service),
) -> TryOnCancelResponse:
    return await service.cancel(user_id=user_id, job_id=job_id)


@router.post("/internal/jobs/{job_id}/claim", response_model=TryOnWorkerClaim, dependencies=[Depends(require_internal_service)])
async def worker_claim(
    job_id: UUID,
    service: TryOnApplicationService = Depends(get_service),
) -> TryOnWorkerClaim:
    result = await service.worker_claim(job_id)
    if result is None:
        from api.app.core.errors import ConflictError
        raise ConflictError("Try-on job is already claimed or unavailable")
    return TryOnWorkerClaim.model_validate(result)


@router.post("/internal/jobs/{job_id}/prepare", response_model=dict, dependencies=[Depends(require_internal_service)])
async def worker_prepare(
    job_id: UUID,
    service: TryOnApplicationService = Depends(get_service),
) -> dict:
    return await service.prepare_execution(job_id=job_id)


@router.post("/internal/jobs/{job_id}/provider", response_model=dict, dependencies=[Depends(require_internal_service)])
async def worker_provider(
    job_id: UUID,
    payload: dict,
    service: TryOnApplicationService = Depends(get_service),
) -> dict:
    provider_job_id = payload.get("provider_job_id")
    if not isinstance(provider_job_id, str) or not provider_job_id:
        from api.app.core.errors import ConflictError
        raise ConflictError("provider_job_id is required")
    await service.set_provider_job(job_id=job_id, provider_job_id=provider_job_id)
    return {"job_id": str(job_id), "provider_job_id": provider_job_id, "status": "inference"}


@router.post("/internal/jobs/{job_id}/progress", response_model=dict, dependencies=[Depends(require_internal_service)])
async def worker_progress(
    job_id: UUID,
    payload: TryOnWorkerProgress,
    service: TryOnApplicationService = Depends(get_service),
) -> dict:
    await service.worker_progress(job_id=job_id, status=payload.status.value)
    return {"job_id": str(job_id), "status": payload.status.value}


@router.post("/internal/jobs/{job_id}/complete", response_model=dict, dependencies=[Depends(require_internal_service)])
async def worker_complete(
    job_id: UUID,
    payload: TryOnWorkerComplete,
    service: TryOnApplicationService = Depends(get_service),
) -> dict:
    return await service.worker_complete(job_id=job_id, result_key=payload.result_key, quality=payload.quality.model_dump())


@router.post("/internal/jobs/{job_id}/fail", response_model=dict, dependencies=[Depends(require_internal_service)])
async def worker_fail(
    job_id: UUID,
    payload: TryOnWorkerFailure,
    service: TryOnApplicationService = Depends(get_service),
) -> dict:
    return await service.worker_fail(job_id=job_id, reason=payload.reason.value, retryable=payload.retryable)
