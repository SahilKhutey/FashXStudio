from uuid import UUID

from pydantic import BaseModel, Field


class ResourceRef(BaseModel):
    id: UUID


class AuditTimestamps(BaseModel):
    created_at: str
    updated_at: str | None = None


class IdempotencyContext(BaseModel):
    key: str = Field(min_length=8, max_length=255)
