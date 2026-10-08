from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commerce_feedback import BuyClick


class CommerceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_buy_click(self, click_id: UUID) -> BuyClick | None:
        return await self.session.get(BuyClick, click_id)
