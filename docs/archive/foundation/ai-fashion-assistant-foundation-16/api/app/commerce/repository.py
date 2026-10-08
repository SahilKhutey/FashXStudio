from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import MerchantOffer
from database.models.commerce_feedback import BuyClick, DomainEvent


class CommerceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_buy_click(self, click_id: UUID) -> BuyClick | None:
        return await self.session.get(BuyClick, click_id)

    async def get_offer(self, offer_id: UUID) -> MerchantOffer | None:
        return await self.session.get(MerchantOffer, offer_id)

    async def create_buy_click(
        self,
        *,
        user_id: UUID,
        garment_id: UUID,
        offer_id: UUID,
        affiliate_network: str,
        tracking_id: str,
    ) -> BuyClick:
        click = BuyClick(
            user_id=user_id,
            garment_id=garment_id,
            offer_id=offer_id,
            affiliate_network=affiliate_network,
            tracking_id=tracking_id,
        )
        self.session.add(click)
        await self.session.flush()
        return click

    async def create_event(
        self,
        *,
        event_id: UUID,
        event_type: str,
        schema_version: int,
        user_id: UUID | None,
        object_type: str | None,
        object_id: UUID | None,
        trace_id: UUID | None,
        occurred_at,
        payload: dict[str, object],
    ) -> DomainEvent:
        event = DomainEvent(
            id=event_id,
            event_type=event_type,
            schema_version=schema_version,
            user_id=user_id,
            object_type=object_type,
            object_id=object_id,
            trace_id=trace_id,
            occurred_at=occurred_at,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event
