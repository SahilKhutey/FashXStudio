from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class AnalyticsEventRecorded(DomainEvent):
    entity_id: UUID | None = None
    event_type: str = ""


@dataclass(frozen=True, slots=True)
class AnalyticsMetricAggregated(DomainEvent):
    entity_id: UUID | None = None
    metric_name: str = ""
