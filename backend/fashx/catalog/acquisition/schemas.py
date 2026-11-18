from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from fashx.catalog.acquisition.contracts_v2 import SyncMode


class SyncTriggerRequest(BaseModel):
    """Admin request payload to trigger catalog source synchronization."""

    mode: SyncMode = Field(
        default=SyncMode.FULL, description="Synchronization mode (full or incremental)"
    )
    limit_per_page: int = Field(default=100, ge=1, le=1000, description="Page batch size")
    apply: bool = Field(default=True, description="Whether to persist changes or run as dry-run")


class SyncRunResponse(BaseModel):
    """Schema representing a catalog synchronization execution record."""

    id: UUID
    source_id: UUID
    mode: str
    status: str
    snapshot_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    pages_fetched: int
    products_seen: int
    products_inserted: int
    products_updated: int
    products_rejected: int
    error_code: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SyncCheckpointResponse(BaseModel):
    """Schema representing durable checkpoint state for a source."""

    id: UUID
    source_id: UUID
    checkpoint_type: str
    cursor_data: dict | None = None
    watermark: datetime | None = None
    provider_version: str | None = None
    last_success_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
