from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import Merchant


class MerchantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, merchant: Merchant) -> Merchant:
        self.session.add(merchant)
        await self.session.flush()
        return merchant

    async def get_by_id(self, merchant_id: UUID) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.id == merchant_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_legal_name(self, legal_name: str) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.legal_name == legal_name)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_registration_reference(self, reg_ref: str) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.registration_reference == reg_ref)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_merchants(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Merchant]:
        stmt = select(Merchant)
        if status:
            stmt = stmt.where(Merchant.verification_status == status)
        stmt = stmt.order_by(Merchant.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update(self, merchant: Merchant) -> Merchant:
        await self.session.flush()
        return merchant
