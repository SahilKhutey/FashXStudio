from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, and_, case, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commerce_feedback import BuyClick, DomainEvent, TryOnFeedback, WardrobeItem
from database.models.identity import User


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_users_created(self, start_at: datetime, end_at: datetime) -> int:
        stmt = select(func.count()).select_from(User).where(User.created_at >= start_at, User.created_at < end_at)
        return int((await self.session.execute(stmt)).scalar_one())

    async def event_counts(self, start_at: datetime, end_at: datetime) -> dict[str, int]:
        stmt = (
            select(DomainEvent.event_type, func.count())
            .where(DomainEvent.occurred_at >= start_at, DomainEvent.occurred_at < end_at)
            .group_by(DomainEvent.event_type)
        )
        rows = (await self.session.execute(stmt)).all()
        return {event_type: int(count) for event_type, count in rows}

    async def distinct_event_users(self, event_type: str, start_at: datetime, end_at: datetime) -> int:
        stmt = (
            select(func.count(distinct(DomainEvent.user_id)))
            .where(
                DomainEvent.event_type == event_type,
                DomainEvent.user_id.is_not(None),
                DomainEvent.occurred_at >= start_at,
                DomainEvent.occurred_at < end_at,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def repeat_event_users(self, event_type: str, start_at: datetime, end_at: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(
                select(DomainEvent.user_id)
                .where(
                    DomainEvent.event_type == event_type,
                    DomainEvent.user_id.is_not(None),
                    DomainEvent.occurred_at >= start_at,
                    DomainEvent.occurred_at < end_at,
                )
                .group_by(DomainEvent.user_id)
                .having(func.count() >= 2)
                .subquery()
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_feedback(self, start_at: datetime, end_at: datetime) -> int:
        stmt = select(func.count()).select_from(TryOnFeedback).where(
            TryOnFeedback.created_at >= start_at,
            TryOnFeedback.created_at < end_at,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_saves(self, start_at: datetime, end_at: datetime) -> int:
        stmt = select(func.count()).select_from(WardrobeItem).where(
            WardrobeItem.saved_at >= start_at,
            WardrobeItem.saved_at < end_at,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_buy_clicks(self, start_at: datetime, end_at: datetime) -> int:
        stmt = select(func.count()).select_from(BuyClick).where(
            BuyClick.clicked_at >= start_at,
            BuyClick.clicked_at < end_at,
        )
        return int((await self.session.execute(stmt)).scalar_one())
