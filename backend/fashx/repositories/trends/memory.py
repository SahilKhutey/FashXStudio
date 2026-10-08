from uuid import UUID

from fashx.domain.trends.entities import (
    Trend,
    TrendObservation,
)
from fashx.domain.trends.repository import (
    TrendObservationRepository,
    TrendRepository,
)


class InMemoryTrendRepository(TrendRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Trend] = {}

    async def get(
        self,
        trend_id: UUID,
    ) -> Trend | None:
        return self._items.get(trend_id)

    async def save(
        self,
        trend: Trend,
    ) -> Trend:
        self._items[trend.id] = trend
        return trend

    async def list_active(
        self,
        *,
        region: str | None = None,
        trend_type: str | None = None,
    ) -> list[Trend]:
        result = [
            trend
            for trend in self._items.values()
            if (
                trend.status.value == "active"
                if hasattr(trend.status, "value")
                else trend.status == "active"
            )
        ]

        if region:
            result = [
                trend
                for trend in result
                if (
                    trend.region is None
                    or trend.region.lower() == region.lower()
                )
            ]

        if trend_type:
            result = [
                trend
                for trend in result
                if (
                    trend.trend_type.value == trend_type
                    if hasattr(trend.trend_type, "value")
                    else str(trend.trend_type) == trend_type
                )
            ]

        return result


class InMemoryTrendObservationRepository(TrendObservationRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, TrendObservation] = {}

    async def save(
        self,
        observation: TrendObservation,
    ) -> TrendObservation:
        self._items[observation.id] = observation
        return observation

    async def list_by_topic(
        self,
        topic: str,
    ) -> list[TrendObservation]:
        normalized = topic.lower().strip()
        return [
            observation
            for observation in self._items.values()
            if observation.topic.lower().strip() == normalized
        ]
