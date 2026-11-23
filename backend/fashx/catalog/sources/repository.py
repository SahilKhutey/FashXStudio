from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource


class CatalogSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, source: CatalogSource) -> CatalogSource:
        self.session.add(source)
        await self.session.flush()
        return source

    async def get_by_id(self, source_id: UUID) -> CatalogSource | None:
        stmt = select(CatalogSource).where(CatalogSource.id == source_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> CatalogSource | None:
        stmt = select(CatalogSource).where(CatalogSource.slug == slug)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_merchant(self, merchant_id: UUID) -> Sequence[CatalogSource]:
        stmt = (
            select(CatalogSource)
            .where(CatalogSource.merchant_id == merchant_id)
            .order_by(CatalogSource.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_sources(
        self,
        merchant_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[CatalogSource]:
        stmt = select(CatalogSource)
        if merchant_id:
            stmt = stmt.where(CatalogSource.merchant_id == merchant_id)
        if status:
            stmt = stmt.where(CatalogSource.source_status == status)
        stmt = stmt.order_by(CatalogSource.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update(self, source: CatalogSource) -> CatalogSource:
        await self.session.flush()
        return source
