from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .base import PermissionAwareAdapter


class FeedAdapter(PermissionAwareAdapter):
    """Adapter for HTTPS/SFTP feed ingestion."""

    def __init__(self, session: AsyncSession, source_id: UUID, feed_url: str = "") -> None:
        super().__init__(session, source_id)
        self.feed_url = feed_url

    async def fetch_batch(self, limit: int = 50) -> list[dict[str, Any]]:
        await self.verify_read_permission()
        return []
