from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    SignalType,
    TrendDirection,
    TrendSource,
    TrendStatus,
    TrendType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class TrendObservation:
    id: UUID = field(default_factory=new_id)
    topic: str = ""
    trend_type: str = "style"
    signal_type: SignalType = SignalType.ENGAGEMENT
    source: TrendSource = TrendSource.CURATED
    value: Decimal = Decimal("0")
    region: str | None = None
    observed_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.value, (int, str)):
            self.value = Decimal(str(self.value))
        elif isinstance(self.value, float):
            self.value = Decimal(str(self.value))
        if isinstance(self.signal_type, str) and not isinstance(self.signal_type, SignalType):
            self.signal_type = SignalType(self.signal_type)
        if isinstance(self.source, str) and not isinstance(self.source, TrendSource):
            self.source = TrendSource(self.source)

    def validate(self) -> None:
        if not self.topic or not self.topic.strip():
            raise ValidationError("Trend observation topic is required.")

        if self.value < 0:
            raise ValidationError("Trend observation value cannot be negative.")


@dataclass(slots=True)
class Trend:
    id: UUID = field(default_factory=new_id)
    topic: str = ""
    trend_type: TrendType = TrendType.STYLE
    status: TrendStatus = TrendStatus.DRAFT
    direction: TrendDirection = TrendDirection.STABLE
    region: str | None = None
    strength: float = 0.0
    momentum: float = 0.0
    confidence: float = 0.0
    observation_count: int = 0
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.trend_type, str) and not isinstance(self.trend_type, TrendType):
            self.trend_type = TrendType(self.trend_type)
        if isinstance(self.status, str) and not isinstance(self.status, TrendStatus):
            self.status = TrendStatus(self.status)
        if isinstance(self.direction, str) and not isinstance(self.direction, TrendDirection):
            self.direction = TrendDirection(self.direction)

    def validate(self) -> None:
        if not self.topic or not self.topic.strip():
            raise ValidationError("Trend topic is required.")

        for name, value in (
            ("strength", self.strength),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValidationError(f"{name} must be between 0 and 1.")

        if not -1.0 <= self.momentum <= 1.0:
            raise ValidationError("Momentum must be between -1 and 1.")

        if self.observation_count < 0:
            raise ValidationError("Observation count cannot be negative.")

        if self.version < 1:
            raise ValidationError("Trend version must be positive.")

        if (
            self.valid_from
            and self.valid_until
            and self.valid_until <= self.valid_from
        ):
            raise ValidationError("Trend validity window is invalid.")

    def touch(self) -> None:
        self.version += 1
        self.updated_at = utc_now()


@dataclass(frozen=True, slots=True)
class TrendContext:
    region: str | None = None
    trend_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = 20


@dataclass(slots=True)
class TrendSnapshot:
    trend_id: UUID
    topic: str
    region: str | None = None
    timestamp: datetime = field(default_factory=utc_now)
    strength: float = 0.0
    momentum: float = 0.0
    confidence: float = 0.0
    direction: TrendDirection = TrendDirection.STABLE
    observation_count: int = 0
    engine_version: str = "1.0.0"
