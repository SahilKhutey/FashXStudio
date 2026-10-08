from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.commerce_feedback import TryOnFeedback

class VisualFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_job(self, *, user_id: UUID, job_id: UUID) -> TryOnFeedback | None:
        stmt = select(TryOnFeedback).where(TryOnFeedback.user_id == user_id, TryOnFeedback.tryon_job_id == job_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, user_id: UUID, job_id: UUID, visual_accuracy: str, purchase_confidence: int | None) -> TryOnFeedback:
        feedback = TryOnFeedback(user_id=user_id, tryon_job_id=job_id,
                                 visual_accuracy=visual_accuracy, purchase_confidence=purchase_confidence)
        self.session.add(feedback)
        await self.session.flush()
        return feedback
