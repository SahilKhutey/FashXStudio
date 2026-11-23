from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .base import PermissionAwareAdapter


class AffiliateApiAdapter(PermissionAwareAdapter):
    """Adapter for affiliate network catalog APIs."""

    def __init__(self, session: AsyncSession, source_id: UUID, network_id: str = "") -> None:
        super().__init__(session, source_id)
        self.network_id = network_id

    async def fetch_batch(self, limit: int = 50) -> list[dict[str, Any]]:
        await self.verify_read_permission()
        return []
