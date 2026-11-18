from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from fashx.catalog.ingestion.authorization_guard import CatalogAuthorizationGuard


class PermissionAwareAdapter(ABC):
    """Base adapter class that strictly checks authorization before executing catalog operations."""

    def __init__(self, session: AsyncSession, source_id: UUID) -> None:
        self.session = session
        self.source_id = source_id
        self.guard = CatalogAuthorizationGuard(session)

    async def verify_read_permission(
        self, product_id: str | None = None, category: str | None = None, market: str | None = None
    ) -> None:
        await self.guard.guard_product_read(
            source_id=self.source_id,
            product_id=product_id,
            category=category,
            market=market,
        )

    async def verify_store_permission(
        self, product_id: str | None = None, category: str | None = None, market: str | None = None
    ) -> None:
        await self.guard.guard_product_store(
            source_id=self.source_id,
            product_id=product_id,
            category=category,
            market=market,
        )

    async def verify_image_fetch_permission(
        self, product_id: str | None = None, category: str | None = None, market: str | None = None
    ) -> None:
        await self.guard.guard_image_fetch(
            source_id=self.source_id,
            product_id=product_id,
            category=category,
            market=market,
        )

    @abstractmethod
    async def fetch_batch(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch a batch of raw product records, guarded by permissions."""
        ...
