from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    AggregationPeriod,
    AnalyticsEventType,
    AnalyticsSource,
    MetricType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class AnalyticsEvent:
    id: UUID = field(default_factory=new_id)
    event_type: AnalyticsEventType = AnalyticsEventType.PAGE_VIEWED
    customer_id: UUID | None = None
    session_id: str | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    category: str | None = None
    brand: str | None = None
    region: str | None = None
    source: AnalyticsSource = AnalyticsSource.SYSTEM
    value: Decimal | None = None
    currency: str | None = None
    properties: dict[str, str] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utc_now)
    correlation_id: UUID | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if isinstance(self.event_type, str) and not isinstance(
            self.event_type, AnalyticsEventType
        ):
            self.event_type = AnalyticsEventType(self.event_type)
        if isinstance(self.source, str) and not isinstance(
            self.source, AnalyticsSource
        ):
            self.source = AnalyticsSource(self.source)
        if self.value is not None and not isinstance(self.value, Decimal):
            self.value = Decimal(str(self.value))

    def validate(self) -> None:
        if self.session_id is None and self.customer_id is None:
            raise ValidationError(
                "Analytics event requires customer_id or session_id."
            )

        if self.value is not None:
            if self.value < Decimal("0"):
                raise ValidationError("Analytics value cannot be negative.")

        if self.currency is not None:
            if len(self.currency) != 3:
                raise ValidationError("Currency must be a 3-character code.")


@dataclass(slots=True)
class AnalyticsMetric:
    name: str
    metric_type: MetricType
    value: Decimal
    period: AggregationPeriod
    period_start: datetime
    dimensions: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.metric_type, str) and not isinstance(
            self.metric_type, MetricType
        ):
            self.metric_type = MetricType(self.metric_type)
        if isinstance(self.period, str) and not isinstance(
            self.period, AggregationPeriod
        ):
            self.period = AggregationPeriod(self.period)
        if not isinstance(self.value, Decimal):
            self.value = Decimal(str(self.value))

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Metric name is required.")

        if self.value < Decimal("0"):
            raise ValidationError("Metric value cannot be negative.")


@dataclass(slots=True)
class AggregationBucket:
    metric_name: str
    period: AggregationPeriod
    period_start: datetime
    dimensions: dict[str, str] = field(default_factory=dict)
    count: int = 0
    total_value: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if isinstance(self.period, str) and not isinstance(
            self.period, AggregationPeriod
        ):
            self.period = AggregationPeriod(self.period)
        if not isinstance(self.total_value, Decimal):
            self.total_value = Decimal(str(self.total_value))

    def add(
        self,
        value: Decimal | None = None,
    ) -> None:
        self.count += 1
        if value is not None:
            self.total_value += (
                value if isinstance(value, Decimal) else Decimal(str(value))
            )
