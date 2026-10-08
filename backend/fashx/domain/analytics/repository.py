from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from .entities import (
    AggregationBucket,
    AnalyticsEvent,
)


class AnalyticsEventRepository(ABC):
    @abstractmethod
    async def get(
        self,
        event_id: UUID,
    ) -> AnalyticsEvent | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        event: AnalyticsEvent,
    ) -> AnalyticsEvent:
        raise NotImplementedError

    @abstractmethod
    async def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[AnalyticsEvent]:
        raise NotImplementedError


class AnalyticsMetricRepository(ABC):
    @abstractmethod
    async def save_bucket(
        self,
        bucket: AggregationBucket,
    ) -> AggregationBucket:
        raise NotImplementedError

    @abstractmethod
    async def get_bucket(
        self,
        metric_name: str,
        period_start: datetime,
        dimensions: dict[str, str],
    ) -> AggregationBucket | None:
        raise NotImplementedError
