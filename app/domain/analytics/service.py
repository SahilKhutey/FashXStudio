from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.core.context import CoreContext
from app.core.event_bus import EventBus

from .aggregation import (
    event_dimensions,
    truncate_timestamp,
)
from .entities import (
    AggregationBucket,
    AnalyticsEvent,
)
from .enums import (
    AggregationPeriod,
)
from .events import (
    AnalyticsEventRecorded,
    AnalyticsMetricAggregated,
)
from .repository import (
    AnalyticsEventRepository,
    AnalyticsMetricRepository,
)


@dataclass(slots=True)
class AnalyticsService:
    event_repository: AnalyticsEventRepository
    metric_repository: AnalyticsMetricRepository
    event_bus: EventBus = field(default_factory=EventBus)

    async def record_event(
        self,
        *,
        context: CoreContext | None = None,
        event: AnalyticsEvent,
    ) -> AnalyticsEvent:
        event.validate()

        if event.correlation_id is None and context is not None:
            event.correlation_id = context.correlation_id

        await self.event_repository.save(event)

        if self.event_bus:
            correlation_id = context.correlation_id if context else None
            event_type_val = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )
            await self.event_bus.publish(
                AnalyticsEventRecorded(
                    entity_id=event.id,
                    event_type=event_type_val,
                    correlation_id=correlation_id,
                )
            )

        return event

    async def aggregate(
        self,
        *,
        start: datetime,
        end: datetime,
        metric_name: str,
        period: AggregationPeriod,
    ) -> list[AggregationBucket]:
        events = await self.event_repository.list_between(
            start,
            end,
        )

        buckets: dict[
            tuple,
            AggregationBucket,
        ] = {}

        for event in events:
            period_start = truncate_timestamp(
                event.occurred_at,
                period,
            )

            dimensions = event_dimensions(event)

            key = (
                period_start,
                tuple(sorted(dimensions.items())),
            )

            bucket = buckets.get(key)
            if bucket is None:
                bucket = AggregationBucket(
                    metric_name=metric_name,
                    period=period,
                    period_start=period_start,
                    dimensions=dimensions,
                )
                buckets[key] = bucket

            value = (
                event.value
                if event.value is not None
                else Decimal("0.00")
            )
            bucket.add(value)

        results = list(buckets.values())

        for bucket in results:
            await self.metric_repository.save_bucket(bucket)
            if self.event_bus:
                await self.event_bus.publish(
                    AnalyticsMetricAggregated(
                        entity_id=None,
                        metric_name=bucket.metric_name,
                    )
                )

        return results
