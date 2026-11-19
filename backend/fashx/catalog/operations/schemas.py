from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.models.catalog_operations import (
    OperationalStatus,
    SyncMode,
)


class SourceConnectionRequest(BaseModel):
    merchant_id: UUID
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    source_type: str = Field(default="MERCHANT_API", max_length=32)
    adapter_name: str = Field(default="generic_merchant_api", max_length=64)
    adapter_version: str = Field(default="1.0.0", max_length=32)
    access_method: str = Field(default="API_KEY", max_length=32)
    credential_secret_ref: str | None = Field(default=None, max_length=512)
    market_codes: list[str] = Field(default_factory=lambda: ["IN"])
    category_codes: list[str] = Field(default_factory=lambda: ["apparel"])
    refresh_hours: int = Field(default=24, ge=1, le=720)


class SourceConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    slug: str
    name: str
    source_type: str
    adapter_name: str | None
    adapter_version: str | None
    access_method: str | None
    masked_credential_ref: str | None
    source_status: str
    operational_status: str
    is_enabled: bool
    created_at: datetime


class SourceOperationalStatusRequest(BaseModel):
    target_status: OperationalStatus
    reason: str = Field(..., min_length=3, max_length=500)


class SourceOperationalStatusResponse(BaseModel):
    source_id: UUID
    operational_status: str
    is_enabled: bool
    updated_at: datetime
    message: str


class ManualSyncRequest(BaseModel):
    sync_mode: SyncMode = SyncMode.INCREMENTAL
    idempotency_key: str | None = Field(default=None, max_length=128)
    force: bool = False


class ManualSyncResponse(BaseModel):
    run_id: UUID
    source_id: UUID
    sync_mode: str
    status: str
    idempotency_key: str | None
    is_duplicate_request: bool
    enqueued_at: datetime


class SourceScheduleRequest(BaseModel):
    enabled: bool = True
    sync_mode: SyncMode = SyncMode.INCREMENTAL
    interval_minutes: int = Field(default=60, ge=15, le=10080)
    cron_expression: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="UTC", max_length=64)


class SourceScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    merchant_id: UUID
    enabled: bool
    sync_mode: str
    interval_minutes: int
    cron_expression: str | None
    timezone: str
    next_run_at: datetime | None
    last_scheduled_at: datetime | None
    updated_at: datetime


class SyncStatusDashboardResponse(BaseModel):
    source_id: UUID
    source_name: str
    operational_status: str
    source_status: str
    last_sync_status: str | None = None
    last_sync_mode: str | None = None
    last_successful_sync_at: datetime | None = None
    last_failed_sync_at: datetime | None = None
    duration_seconds: float | None = None
    counts: dict = Field(default_factory=dict)
    last_error: str | None = None
    is_healthy: bool = True


class IngestRunErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingest_run_id: UUID
    source_id: UUID
    error_code: str
    error_category: str
    failed_stage: str
    source_product_reference: str | None
    safe_error_message: str
    retryable: bool
    attempt_number: int
    occurred_at: datetime
    resolved_at: datetime | None


class IngestErrorListResponse(BaseModel):
    errors: list[IngestRunErrorResponse]
    total_count: int
    page: int
    page_size: int


class QuarantineResolutionGuidance(BaseModel):
    reason_code: str
    severity: str  # BLOCKING | WARNING
    summary: str
    recommended_action: str


class QuarantinedProductResponse(BaseModel):
    id: UUID
    source_id: UUID
    ingest_run_id: UUID
    source_product_id: str | None
    reason_code: str
    field_name: str | None
    guidance: QuarantineResolutionGuidance
    first_seen_at: datetime
    status: str


class QuarantineReportListResponse(BaseModel):
    records: list[QuarantinedProductResponse]
    total_count: int


class ImagePermissionMatrixResponse(BaseModel):
    source_id: UUID
    merchant_id: UUID
    fetch_permitted: bool
    store_permitted: bool
    display_permitted: bool
    ai_processing_permitted: bool
    vto_permitted: bool
    derivatives_retained: bool
    total_assets_count: int
    active_assets_count: int
    suspended_assets_count: int
    warning_messages: list[str] = Field(default_factory=list)


class SourceTakedownRequest(BaseModel):
    reason_code: str = Field(..., min_length=2, max_length=80)
    reason_text: str = Field(..., min_length=5, max_length=1000)
    purge_images: bool = True


class SourceTakedownResponse(BaseModel):
    source_id: UUID
    takedown_status: str
    jobs_cancelled_count: int
    offers_deactivated_count: int
    images_purged_count: int
    completed_at: datetime


class MerchantProductOverrideRequest(BaseModel):
    field_name: str = Field(..., min_length=2, max_length=64)
    override_value: dict
    reason: str | None = Field(default=None, max_length=500)


class MerchantProductOverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    merchant_product_id: UUID
    field_name: str
    override_value: dict
    previous_value: dict | None
    reason: str | None
    updated_at: datetime


class MerchantOfferDeactivateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class MerchantOfferDeactivateResponse(BaseModel):
    offer_id: UUID
    merchant_id: UUID
    garment_id: UUID
    offer_status: str
    canonical_garment_active: bool
    deactivated_at: datetime


class CatalogAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    actor_role: str
    merchant_id: UUID | None
    source_id: UUID | None
    entity_type: str
    entity_id: str | None
    action: str
    reason_code: str | None
    safe_change_summary: dict
    outcome: str
    created_at: datetime


class CatalogAuditListResponse(BaseModel):
    events: list[CatalogAuditEventResponse]
    total_count: int
