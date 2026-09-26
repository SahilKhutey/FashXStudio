from abc import ABC, abstractmethod
from decimal import Decimal

from .entities import TrendObservation
from .enums import (
    SignalType,
    TrendSource,
)


class TrendDataProvider(ABC):
    @abstractmethod
    async def collect(
        self,
        *,
        region: str | None = None,
    ) -> list[TrendObservation]:
        raise NotImplementedError


class TestTrendProvider(TrendDataProvider):
    async def collect(
        self,
        *,
        region: str | None = None,
    ) -> list[TrendObservation]:
        return [
            TrendObservation(
                topic="oversized jacket",
                trend_type="style",
                signal_type=SignalType.SEARCH_VOLUME,
                source=TrendSource.SEARCH,
                value=Decimal("9200"),
                region=region,
            ),
            TrendObservation(
                topic="cargo pants",
                trend_type="category",
                signal_type=SignalType.ENGAGEMENT,
                source=TrendSource.INTERNAL_BEHAVIOR,
                value=Decimal("0.81"),
                region=region,
            ),
        ]
