from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4
from api.app.core.errors import ConflictError, NotFoundError
from api.app.core.transactions import transaction
from api.app.events.repository import EventRepository
from api.app.feedback.repository import VisualFeedbackRepository
from api.app.tryon.repositories.tryon import TryOnRepository
from schemas.feedback.visual import TryOnFeedbackCreate, TryOnFeedbackResponse

class TryOnFeedbackService:
    def __init__(self, *, session, feedback: VisualFeedbackRepository, tryon: TryOnRepository) -> None:
        self.session = session
        self.feedback = feedback
        self.tryon = tryon

    async def submit(self, *, user_id: UUID, request: TryOnFeedbackCreate, trace_id: UUID | None) -> TryOnFeedbackResponse:
        async with transaction(self.session):
            job = await self.tryon.get_by_id_for_user(user_id=user_id, job_id=request.tryon_job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            if job.status != "completed":
                raise ConflictError("Feedback is only available for completed try-on jobs")
            existing = await self.feedback.get_for_job(user_id=user_id, job_id=request.tryon_job_id)
            if existing is not None:
                raise ConflictError("Try-on feedback has already been submitted")
            feedback = await self.feedback.create(user_id=user_id, job_id=request.tryon_job_id,
                                                   visual_accuracy=request.visual_accuracy.value,
                                                   purchase_confidence=request.purchase_confidence)
            await EventRepository(self.session).create(
                event_id=uuid4(), event_type="tryon_feedback_submitted", schema_version=1,
                user_id=user_id, object_type="tryon_job", object_id=request.tryon_job_id,
                trace_id=trace_id, occurred_at=datetime.now(timezone.utc),
                payload={"feedback_id": str(feedback.id), "visual_accuracy": request.visual_accuracy.value,
                         "purchase_confidence": request.purchase_confidence},
            )
            return TryOnFeedbackResponse(
                feedback_id=feedback.id, tryon_job_id=feedback.tryon_job_id,
                visual_accuracy=request.visual_accuracy, purchase_confidence=feedback.purchase_confidence,
                created_at=feedback.created_at.isoformat() if feedback.created_at else datetime.now(timezone.utc).isoformat())
