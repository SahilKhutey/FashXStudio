from decimal import Decimal

from pydantic import BaseModel, Field


class TrendObservationRequest(BaseModel):
    topic: str
    trend_type: str = "style"
    signal_type: str = "engagement"
    source: str = "curated"
    value: Decimal = Field(ge=0)
    region: str | None = None


class TrendCreateRequest(BaseModel):
    topic: str
    trend_type: str = "style"
    region: str | None = None
    strength: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
    momentum: float = Field(
        default=0.0,
        ge=-1,
        le=1,
    )
    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
