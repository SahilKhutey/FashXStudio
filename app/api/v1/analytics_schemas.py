from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsEventRequest(BaseModel):
    event_type: str
    customer_id: UUID | None = None
    session_id: str | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    category: str | None = None
    brand: str | None = None
    region: str | None = None
    value: Decimal | None = None
    currency: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class AnalyticsAggregateRequest(BaseModel):
    start: datetime
    end: datetime
    metric_name: str
    period: str = "day"
