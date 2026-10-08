from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Trend,
    TrendObservation,
)


class TrendRepository(ABC):
    @abstractmethod
    async def get(
        self,
        trend_id: UUID,
    ) -> Trend | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        trend: Trend,
    ) -> Trend:
        raise NotImplementedError

    @abstractmethod
    async def list_active(
        self,
        *,
        region: str | None = None,
        trend_type: str | None = None,
    ) -> list[Trend]:
        raise NotImplementedError


class TrendObservationRepository(ABC):
    @abstractmethod
    async def save(
        self,
        observation: TrendObservation,
    ) -> TrendObservation:
        raise NotImplementedError

    @abstractmethod
    async def list_by_topic(
        self,
        topic: str,
    ) -> list[TrendObservation]:
        raise NotImplementedError
