"""
Try-On Repository (Rule I04 & I07)
Persistence operations for Try-On jobs with atomic concurrency claiming.
"""

import uuid
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.models import TryOnJobModel


class TryOnRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[TryOnJobModel]:
        stmt = select(TryOnJobModel).where(TryOnJobModel.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_successful_by_cache_key(self, cache_key: str) -> Optional[TryOnJobModel]:
        """Finds latest completed try-on result matching the exact composite cache key."""
        stmt = (
            select(TryOnJobModel)
            .where(TryOnJobModel.cache_key == cache_key)
            .where(TryOnJobModel.status == "completed")
            .order_by(TryOnJobModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_job(
        self,
        user_id: uuid.UUID,
        canonical_id: uuid.UUID,
        user_photo_id: str,
        cache_key: str,
    ) -> TryOnJobModel:
        job = TryOnJobModel(
            job_id=uuid.uuid4(),
            user_id=user_id,
            canonical_id=canonical_id,
            user_photo_id=user_photo_id,
            status="queued",
            cache_key=cache_key,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def claim_job_atomically(
        self,
        job_id: uuid.UUID,
        worker_id: str,
    ) -> Optional[TryOnJobModel]:
        """
        Rule I07: Atomically claims a queued job for a specific worker.
        Returns the updated TryOnJobModel if claim was won, None if already claimed.
        """
        stmt = (
            update(TryOnJobModel)
            .where(TryOnJobModel.job_id == job_id)
            .where(TryOnJobModel.status == "queued")
            .values(status="processing", worker_id=worker_id)
            .returning(TryOnJobModel)
        )
        result = await self.session.execute(stmt)
        claimed_job = result.scalar_one_or_none()
        if claimed_job:
            await self.session.commit()
        return claimed_job

    async def complete_job(
        self,
        job_id: uuid.UUID,
        result_image_url: str,
        inference_ms: int,
    ) -> Optional[TryOnJobModel]:
        stmt = (
            update(TryOnJobModel)
            .where(TryOnJobModel.job_id == job_id)
            .values(
                status="completed",
                result_image_url=result_image_url,
                inference_duration_ms=inference_ms,
            )
            .returning(TryOnJobModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def fail_job(
        self,
        job_id: uuid.UUID,
        error_code: str,
        error_message: str,
    ) -> Optional[TryOnJobModel]:
        stmt = (
            update(TryOnJobModel)
            .where(TryOnJobModel.job_id == job_id)
            .values(
                status="failed",
                error_code=error_code,
                error_message=error_message,
            )
            .returning(TryOnJobModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()
