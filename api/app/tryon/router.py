from typing import Any
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.database import get_session_factory
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.tryon.application.get_job_status import (
    GetTryOnJobStatusUseCase,
)
from api.app.tryon.application.submit_job import (
    SubmitTryOnJobCommand,
    SubmitTryOnJobUseCase,
)
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from schemas.common.enums import TryOnFailureReason, TryOnStatus

router = APIRouter(prefix="/tryon", tags=["try-on"])


def get_tryon_uow() -> TryOnUnitOfWork:
    return TryOnUnitOfWork(get_session_factory())


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())


class CreateTryOnJobRequest(BaseModel):
    user_id: UUID
    garment_id: UUID
    render_config: dict[str, Any] | None = None


class TryOnJobSubmissionResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
    artifact_key: str
    is_cached: bool
    result_url: str | None = None


class TryOnJobStatusResponse(BaseModel):
    job_id: UUID
    status: TryOnStatus
    artifact_key: str
    result_url: str | None = None
    failure_reason: TryOnFailureReason | None = None
    model_version: str
    pipeline_version: str


class TryOnArtifactResponse(BaseModel):
    artifact_key: str
    result_key: str
    model_version: str
    pipeline_version: str
    photo_version: int
    garment_version: int


@router.post(
    "/jobs",
    response_model=TryOnJobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_tryon_job(
    request: CreateTryOnJobRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Unique client idempotency key",
    ),
    tryon_uow: TryOnUnitOfWork = Depends(get_tryon_uow),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> TryOnJobSubmissionResponse:
    """Rule I06: Enqueue an asynchronous Try-On job returning 202 Accepted immediately."""
    use_case = SubmitTryOnJobUseCase(
        tryon_uow=tryon_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    cmd = SubmitTryOnJobCommand(
        user_id=request.user_id,
        garment_id=request.garment_id,
        idempotency_key=idempotency_key,
        render_config=request.render_config,
    )
    result = await use_case.execute(cmd)
    return TryOnJobSubmissionResponse(
        job_id=result.job_id,
        status=TryOnStatus(result.status),
        artifact_key=result.artifact_key,
        is_cached=result.is_cached,
        result_url=result.result_url,
    )


@router.get("/jobs/{job_id}", response_model=TryOnJobStatusResponse)
async def get_tryon_job_status(
    job_id: UUID,
    tryon_uow: TryOnUnitOfWork = Depends(get_tryon_uow),
) -> TryOnJobStatusResponse:
    """Retrieve asynchronous try-on job status and artifact URL."""
    use_case = GetTryOnJobStatusUseCase(tryon_uow=tryon_uow)
    res = await use_case.execute(job_id)
    fail_reason = TryOnFailureReason(res.failure_reason) if res.failure_reason else None
    return TryOnJobStatusResponse(
        job_id=res.job_id,
        status=TryOnStatus(res.status),
        artifact_key=res.artifact_key,
        result_url=res.result_url,
        failure_reason=fail_reason,
        model_version=res.model_version,
        pipeline_version=res.pipeline_version,
    )


@router.get("/artifacts/{artifact_key}", response_model=TryOnArtifactResponse)
async def get_tryon_artifact(
    artifact_key: str,
    tryon_uow: TryOnUnitOfWork = Depends(get_tryon_uow),
) -> TryOnArtifactResponse:
    """Retrieve rendered try-on artifact by composite cache key."""
    async with tryon_uow:
        artifact = await tryon_uow.artifacts.get_by_artifact_key(artifact_key)
        if artifact is None:
            from api.app.core.errors import EntityNotFoundError

            raise EntityNotFoundError("TryOnArtifact", artifact_key)

        return TryOnArtifactResponse(
            artifact_key=artifact.artifact_key,
            result_key=artifact.result_key,
            model_version=artifact.model_version,
            pipeline_version=artifact.pipeline_version,
            photo_version=artifact.photo_version,
            garment_version=artifact.garment_version,
        )
