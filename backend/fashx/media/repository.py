from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.media import MediaUpload, UserMedia


class MediaRepository:
    """Async repository for user_media and media_uploads tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_upload(self, upload: MediaUpload) -> MediaUpload:
        self.session.add(upload)
        await self.session.commit()
        await self.session.refresh(upload)
        return upload

    async def get_upload(
        self,
        upload_id: UUID,
        user_id: UUID | None = None,
    ) -> MediaUpload | None:
        stmt = select(MediaUpload).where(MediaUpload.id == upload_id)
        if user_id is not None:
            stmt = stmt.where(MediaUpload.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_upload_for_validation(
        self,
        upload_id: UUID,
        image_id: UUID,
        user_id: UUID,
    ) -> MediaUpload | None:
        stmt = (
            select(MediaUpload)
            .where(MediaUpload.id == upload_id)
            .where(MediaUpload.image_id == image_id)
            .where(MediaUpload.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_upload_status(
        self,
        upload_id: UUID,
        status: str,
        completed_at: datetime | None = None,
        failure_code: str | None = None,
    ) -> None:
        values: dict[str, object] = {"status": status}
        if completed_at is not None:
            values["completed_at"] = completed_at
        if failure_code is not None:
            values["failure_code"] = failure_code
        await self.session.execute(
            update(MediaUpload)
            .where(MediaUpload.id == upload_id)
            .values(**values)
        )
        await self.session.commit()

    async def create_user_media(self, media: UserMedia) -> UserMedia:
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get_user_media(
        self,
        image_id: UUID,
        user_id: UUID | None = None,
    ) -> UserMedia | None:
        stmt = select(UserMedia).where(UserMedia.id == image_id)
        if user_id is not None:
            stmt = stmt.where(UserMedia.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_media_deletion_pending(
        self,
        image_id: UUID,
        user_id: UUID,
    ) -> UserMedia | None:
        media = await self.get_user_media(image_id=image_id, user_id=user_id)
        if media is None:
            return None
        media.status = "DELETION_PENDING"
        media.updated_at = datetime.now(UTC)
        await self.session.commit()
        return media

    async def mark_media_deleted(self, image_id: UUID) -> None:
        now = datetime.now(UTC)
        await self.session.execute(
            update(UserMedia)
            .where(UserMedia.id == image_id)
            .values(status="DELETED", deleted_at=now, updated_at=now)
        )
        await self.session.commit()

    async def count_recent_uploads(self, user_id: UUID, since: datetime) -> int:
        stmt = (
            select(func.count(MediaUpload.id))
            .where(MediaUpload.user_id == user_id)
            .where(MediaUpload.created_at >= since)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def count_pending_uploads(self, user_id: UUID) -> int:
        stmt = (
            select(func.count(MediaUpload.id))
            .where(MediaUpload.user_id == user_id)
            .where(MediaUpload.status.in_(["PENDING_UPLOAD", "VALIDATING"]))
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_total_media_size(self, user_id: UUID) -> int:
        stmt = (
            select(func.coalesce(func.sum(UserMedia.size_bytes), 0))
            .where(UserMedia.user_id == user_id)
            .where(UserMedia.status == "AVAILABLE")
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)
