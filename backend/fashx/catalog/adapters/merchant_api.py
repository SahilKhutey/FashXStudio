from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .base import PermissionAwareAdapter


class MerchantApiAdapter(PermissionAwareAdapter):
    """Adapter for direct merchant REST/GraphQL APIs."""

    def __init__(self, session: AsyncSession, source_id: UUID, base_url: str = "") -> None:
        super().__init__(session, source_id)
        self.base_url = base_url

    async def fetch_batch(self, limit: int = 50) -> list[dict[str, Any]]:
        await self.verify_read_permission()
        # In a real integration, this calls the external merchant endpoint
        return []
