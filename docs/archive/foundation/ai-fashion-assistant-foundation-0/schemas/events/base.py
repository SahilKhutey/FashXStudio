from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: UUID
    event_type: str
    schema_version: int = Field(default=1, ge=1)
    user_id: UUID | None = None
    object_type: str | None = None
    object_id: UUID | None = None
    trace_id: UUID | None = None
    occurred_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)
