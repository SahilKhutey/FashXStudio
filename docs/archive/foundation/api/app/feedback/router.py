from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.core.dependencies import db_session, visual_feedback_repository
from api.app.feedback.application import TryOnFeedbackService
from api.app.feedback.repository import VisualFeedbackRepository
from api.app.tryon.repositories.tryon import TryOnRepository
from schemas.feedback.visual import TryOnFeedbackCreate, TryOnFeedbackResponse

router = APIRouter(prefix="/api/v1/tryon", tags=["try-on-feedback"])

@router.post("/{job_id}/feedback", response_model=TryOnFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    job_id: UUID,
    payload: TryOnFeedbackCreate,
    request: Request,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(db_session),
    feedback: VisualFeedbackRepository = Depends(visual_feedback_repository),
) -> TryOnFeedbackResponse:
    if payload.tryon_job_id != job_id:
        from api.app.core.errors import ConflictError
        raise ConflictError("Path job_id and payload tryon_job_id must match")
    service = TryOnFeedbackService(session=session, feedback=feedback, tryon=TryOnRepository(session))
    trace_raw = getattr(request.state, "trace_id", None)
    trace_id = UUID(trace_raw) if trace_raw else None
    return await service.submit(user_id=user_id, request=payload, trace_id=trace_id)
