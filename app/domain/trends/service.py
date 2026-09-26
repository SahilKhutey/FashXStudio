from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus

from .entities import (
    Trend,
    TrendObservation,
)
from .enums import TrendStatus
from .events import (
    TrendActivated,
    TrendCreated,
    TrendObservationCreated,
)
from .lifecycle import validate_trend_transition
from .repository import (
    TrendObservationRepository,
    TrendRepository,
)


@dataclass(slots=True)
class TrendService:
    trend_repository: TrendRepository
    observation_repository: TrendObservationRepository
    event_bus: EventBus = field(default_factory=EventBus)

    async def create_observation(
        self,
        *,
        context: CoreContext | None = None,
        observation: TrendObservation,
    ) -> TrendObservation:
        observation.validate()

        await self.observation_repository.save(observation)

        correlation_id = context.correlation_id if context else None
        if self.event_bus:
            await self.event_bus.publish(
                TrendObservationCreated(
                    entity_id=observation.id,
                    topic=observation.topic,
                    correlation_id=correlation_id,
                )
            )

        return observation

    async def create_trend(
        self,
        *,
        context: CoreContext | None = None,
        trend: Trend,
    ) -> Trend:
        trend.validate()

        await self.trend_repository.save(trend)

        correlation_id = context.correlation_id if context else None
        if self.event_bus:
            await self.event_bus.publish(
                TrendCreated(
                    entity_id=trend.id,
                    topic=trend.topic,
                    correlation_id=correlation_id,
                )
            )

        return trend

    async def get_trend(
        self,
        trend_id: UUID,
    ) -> Trend:
        trend = await self.trend_repository.get(trend_id)

        if trend is None:
            raise NotFoundError("Trend not found.")

        return trend

    async def list_trends(
        self,
        *,
        region: str | None = None,
        trend_type: str | None = None,
    ) -> list[Trend]:
        return await self.trend_repository.list_active(
            region=region,
            trend_type=trend_type,
        )

    async def activate_trend(
        self,
        trend_id: UUID,
        *,
        context: CoreContext | None = None,
    ) -> Trend:
        trend = await self.get_trend(trend_id)
        validate_trend_transition(trend.status, TrendStatus.ACTIVE)
        trend.status = TrendStatus.ACTIVE
        trend.touch()
        await self.trend_repository.save(trend)

        correlation_id = context.correlation_id if context else None
        if self.event_bus:
            await self.event_bus.publish(
                TrendActivated(
                    entity_id=trend.id,
                    topic=trend.topic,
                    correlation_id=correlation_id,
                )
            )

        return trend
