from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .base import PermissionAwareAdapter


class PartnerExportAdapter(PermissionAwareAdapter):
    """Adapter for partner batch exports and manual drops."""

    def __init__(self, session: AsyncSession, source_id: UUID, export_path: str = "") -> None:
        super().__init__(session, source_id)
        self.export_path = export_path

    async def fetch_batch(self, limit: int = 50) -> list[dict[str, Any]]:
        await self.verify_read_permission()
        return []
