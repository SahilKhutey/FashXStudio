from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.models.catalog_auth import TakedownReasonCode


class TakedownRequestCreate(BaseModel):
    source_id: UUID
    reason_code: TakedownReasonCode
    requested_by: str = Field(..., min_length=2, max_length=255)
    request_reference: str | None = Field(default=None, max_length=512)
    resolution_notes: str | None = None
    assigned_reviewer: UUID | None = None


class TakedownResolutionRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3)
    reviewer_id: UUID


class TakedownResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    reason_code: str
    requested_by: str
    request_reference: str | None = None
    status: str
    received_at: datetime
    acknowledged_at: datetime | None = None
    completed_at: datetime | None = None
    affected_product_count: int = 0
    affected_asset_count: int = 0
    assigned_reviewer: UUID | None = None
    resolution_notes: str | None = None
