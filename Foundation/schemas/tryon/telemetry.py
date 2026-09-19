from enum import StrEnum
from pydantic import BaseModel, Field


class TryOnTelemetryEvent(StrEnum):
    VIEWED = "viewed"
    RETRY_REQUESTED = "retry_requested"


class TryOnTelemetryCreate(BaseModel):
    event: TryOnTelemetryEvent
    elapsed_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    screen_context: str | None = Field(default=None, max_length=64)


class TryOnTelemetryResponse(BaseModel):
    accepted: bool = True
