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


class IngestionJobCreateRequest(BaseModel):
    """Admin request to launch a catalog ingestion run."""

    source_id: UUID
    mode: str = Field(default="incremental", description="Sync mode: full | incremental | manual")
    dry_run: bool = Field(default=False, description="Simulate ingestion without DB commit")
    limit_per_page: int = Field(default=100, ge=1, le=1000)


class IngestionJobResponse(BaseModel):
    """Schema for ingestion run execution details."""

    id: UUID
    source_id: UUID
    merchant_id: UUID | None = None
    sync_mode: str | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    counts: dict
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class IngestionJobReportResponse(BaseModel):
    """Detailed summary metrics for an ingestion run."""

    run_id: UUID
    source_id: UUID
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    counts: dict
    rejection_reasons: dict
    image_counts: dict
    error: str | None = None


class QuarantineRecordResponse(BaseModel):
    """Sanitized quarantined product record."""

    id: UUID
    ingest_run_id: UUID
    source_id: UUID
    source_product_id: str | None = None
    reason_code: str
    field_name: str | None = None
    safe_record_reference: dict | None = None
    record_hash: str | None = None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None

    model_config = ConfigDict(from_attributes=True)


class QuarantineListResponse(BaseModel):
    """Paginated list of quarantined product records."""

    items: list[QuarantineRecordResponse]
    total: int
    limit: int
    offset: int


class QuarantineReprocessResponse(BaseModel):
    """Result of attempting to reprocess a quarantined record."""

    id: UUID
    status: str
    message: str
