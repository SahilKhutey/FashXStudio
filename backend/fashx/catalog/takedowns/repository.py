from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_auth import CatalogTakedownRequest


class CatalogTakedownRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, takedown: CatalogTakedownRequest) -> CatalogTakedownRequest:
        self.session.add(takedown)
        await self.session.flush()
        return takedown

    async def get_by_id(self, takedown_id: UUID) -> CatalogTakedownRequest | None:
        stmt = select(CatalogTakedownRequest).where(CatalogTakedownRequest.id == takedown_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_source(self, source_id: UUID) -> Sequence[CatalogTakedownRequest]:
        stmt = (
            select(CatalogTakedownRequest)
            .where(CatalogTakedownRequest.source_id == source_id)
            .order_by(CatalogTakedownRequest.received_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update(self, takedown: CatalogTakedownRequest) -> CatalogTakedownRequest:
        await self.session.flush()
        return takedown
