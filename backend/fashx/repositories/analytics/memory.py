from datetime import UTC, datetime
from uuid import UUID

from app.domain.analytics.entities import (
    AggregationBucket,
    AnalyticsEvent,
)
from app.domain.analytics.repository import (
    AnalyticsEventRepository,
    AnalyticsMetricRepository,
)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class InMemoryAnalyticsEventRepository(AnalyticsEventRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, AnalyticsEvent] = {}

    async def get(
        self,
        event_id: UUID,
    ) -> AnalyticsEvent | None:
        return self._items.get(event_id)

    async def save(
        self,
        event: AnalyticsEvent,
    ) -> AnalyticsEvent:
        self._items[event.id] = event
        return event

    async def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[AnalyticsEvent]:
        start_utc = _as_utc(start)
        end_utc = _as_utc(end)
        return [
            event
            for event in self._items.values()
            if start_utc <= _as_utc(event.occurred_at) < end_utc
        ]


class InMemoryAnalyticsMetricRepository(AnalyticsMetricRepository):
    def __init__(self) -> None:
        self._items: dict[tuple, AggregationBucket] = {}

    def _key(
        self,
        metric_name: str,
        period_start: datetime,
        dimensions: dict[str, str],
    ) -> tuple:
        dimension_key = tuple(sorted(dimensions.items()))
        return (
            metric_name,
            _as_utc(period_start),
            dimension_key,
        )

    async def save_bucket(
        self,
        bucket: AggregationBucket,
    ) -> AggregationBucket:
        key = self._key(
            bucket.metric_name,
            bucket.period_start,
            bucket.dimensions,
        )
        self._items[key] = bucket
        return bucket

    async def get_bucket(
        self,
        metric_name: str,
        period_start: datetime,
        dimensions: dict[str, str],
    ) -> AggregationBucket | None:
        return self._items.get(
            self._key(
                metric_name,
                period_start,
                dimensions,
            )
        )
