from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from fashx.core.database import get_session_factory
from fashx.security.deps import Principal, get_principal
from fashx.tryon.feedback.schemas import (
    TryOnFeedbackRequest,
    TryOnFeedbackResponse,
)
from fashx.tryon.feedback.service import (
    FeedbackInvalidJobState,
    FeedbackRateLimitExceeded,
    FeedbackSecurityError,
    TryOnFeedbackService,
)
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

router = APIRouter(prefix="/tryon", tags=["tryon-feedback"])

_feedback_service_singleton = TryOnFeedbackService()


def get_feedback_service() -> TryOnFeedbackService:
    return _feedback_service_singleton


def get_tryon_uow() -> TryOnUnitOfWork:
    return TryOnUnitOfWork(get_session_factory())


@router.post(
    "/jobs/{job_id}/feedback",
    response_model=TryOnFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_job_feedback(
    job_id: UUID,
    payload: TryOnFeedbackRequest,
    principal: Principal = Depends(get_principal),
    feedback_service: TryOnFeedbackService = Depends(get_feedback_service),
    tryon_uow: TryOnUnitOfWork = Depends(get_tryon_uow),
) -> TryOnFeedbackResponse:
    """Submit structured feedback/report for an inaccurate or misleading try-on result.

    Verifies job ownership, ensures job is completed, enforces rate limits,
    and records shopper feedback.
    """
    try:
        user_uuid = UUID(principal.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid principal user ID",
        )

    # Verify job existence and ownership in DB
    async with tryon_uow:
        job = await tryon_uow.jobs.get_by_id(job_id)
        if job is None:
            # Don't leak whether the job exists for another user
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"TryOn job '{job_id}' not found.",
            )
        if job.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only submit feedback for your own try-on jobs.",
            )
        job_status = job.status
        provider = getattr(job, "provider", "fashn")
        model_version = getattr(job, "model_version", "v1.5")

    try:
        return await feedback_service.submit_feedback(
            authenticated_user_id=user_uuid,
            job_id=job_id,
            request=payload,
            job_owner_id=user_uuid,
            job_status=job_status,
            has_result=(job_status == "completed"),
            provider=provider,
            model_version=model_version,
        )
    except FeedbackRateLimitExceeded as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except FeedbackInvalidJobState as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except FeedbackSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/jobs/{job_id}/feedback",
    response_model=TryOnFeedbackResponse,
)
async def get_job_feedback(
    job_id: UUID,
    principal: Principal = Depends(get_principal),
    feedback_service: TryOnFeedbackService = Depends(get_feedback_service),
    tryon_uow: TryOnUnitOfWork = Depends(get_tryon_uow),
) -> TryOnFeedbackResponse:
    """Retrieve existing feedback report for a try-on job (owner-restricted)."""
    try:
        user_uuid = UUID(principal.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid principal user ID",
        )

    cache_key = (str(user_uuid), str(job_id))
    feedback_id = feedback_service._job_feedback_index.get(cache_key)
    if not feedback_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No feedback recorded for job '{job_id}'.",
        )

    try:
        return await feedback_service.get_feedback(
            authenticated_user_id=user_uuid,
            feedback_id=feedback_id,
        )
    except FeedbackSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback '{feedback_id}' not found.",
        )
