from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .catalog import CatalogSource, IngestRun, Merchant, MerchantProduct


class OperationalStatus(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"


class SyncMode(StrEnum):
    INCREMENTAL = "INCREMENTAL"
    FULL = "FULL"
    VALIDATION_ONLY = "VALIDATION_ONLY"


class ErrorCategory(StrEnum):
    AUTHENTICATION = "AUTHENTICATION"
    NETWORK = "NETWORK"
    RATE_LIMIT = "RATE_LIMIT"
    DATA_FORMAT = "DATA_FORMAT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INTERNAL = "INTERNAL"


class FailedStage(StrEnum):
    FETCH = "FETCH"
    PARSE = "PARSE"
    VALIDATE = "VALIDATE"
    NORMALIZE = "NORMALIZE"
    PERSIST = "PERSIST"
    IMAGE = "IMAGE"


class AuditAction(StrEnum):
    SOURCE_CONNECTED = "SOURCE_CONNECTED"
    SOURCE_STATUS_CHANGED = "SOURCE_STATUS_CHANGED"
    SYNC_TRIGGERED = "SYNC_TRIGGERED"
    SCHEDULE_UPDATED = "SCHEDULE_UPDATED"
    PRODUCT_OVERRIDE_SET = "PRODUCT_OVERRIDE_SET"
    OFFER_DEACTIVATED = "OFFER_DEACTIVATED"
    TAKEDOWN_REQUESTED = "TAKEDOWN_REQUESTED"


class AuditActorRole(StrEnum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    MERCHANT_OPERATOR = "MERCHANT_OPERATOR"
    SYSTEM = "SYSTEM"


class AuditOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"


class CatalogSourceSchedule(Base, UUIDPrimaryKeyMixin):
    """Configured synchronization schedule and interval cadence for a catalog source."""

    __tablename__ = "catalog_source_schedules"
    __table_args__ = (
        UniqueConstraint("source_id", name="uq_source_schedules_source"),
        Index("ix_source_schedules_next_run", "next_run_at"),
        Index("ix_source_schedules_merchant", "merchant_id"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    sync_mode: Mapped[str] = mapped_column(
        String(32), default=SyncMode.INCREMENTAL.value, server_default="INCREMENTAL", nullable=False
    )
    interval_minutes: Mapped[int] = mapped_column(
        Integer, default=60, server_default="60", nullable=False
    )
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64), default="UTC", server_default="UTC", nullable=False
    )
    last_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    source: Mapped[CatalogSource | None] = relationship(foreign_keys=[source_id])
    merchant: Mapped[Merchant | None] = relationship(foreign_keys=[merchant_id])


class IngestRunError(Base, UUIDPrimaryKeyMixin):
    """Granular error logs for sync and ingestion failures with redaction and retry classification."""

    __tablename__ = "ingest_run_errors"
    __table_args__ = (
        Index("ix_ingest_run_errors_run", "ingest_run_id"),
        Index("ix_ingest_run_errors_source", "source_id"),
        Index("ix_ingest_run_errors_category", "error_category"),
    )

    ingest_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest_runs.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    error_code: Mapped[str] = mapped_column(String(80), nullable=False)
    error_category: Mapped[str] = mapped_column(
        String(40), default=ErrorCategory.INTERNAL.value, server_default="INTERNAL", nullable=False
    )
    failed_stage: Mapped[str] = mapped_column(
        String(40), default=FailedStage.FETCH.value, server_default="FETCH", nullable=False
    )
    source_product_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    safe_error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retryable: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ingest_run: Mapped[IngestRun | None] = relationship(foreign_keys=[ingest_run_id])
    source: Mapped[CatalogSource | None] = relationship(foreign_keys=[source_id])


class CatalogSourceAuditEvent(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail for all operational and administrative actions on catalog sources."""

    __tablename__ = "catalog_source_audit_events"
    __table_args__ = (
        Index("ix_catalog_source_audit_merchant", "merchant_id", "created_at"),
        Index("ix_catalog_source_audit_source", "source_id", "created_at"),
        Index("ix_catalog_source_audit_actor", "actor_id", "created_at"),
    )

    actor_id: Mapped[UUID | None] = mapped_column(nullable=True)
    actor_role: Mapped[str] = mapped_column(
        String(40), default=AuditActorRole.SYSTEM.value, server_default="SYSTEM", nullable=False
    )
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="SET NULL"), nullable=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    safe_change_summary: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(30), default=AuditOutcome.SUCCESS.value, server_default="SUCCESS", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MerchantProductOverride(Base, UUIDPrimaryKeyMixin):
    """Merchant-managed field overrides for ingested products."""

    __tablename__ = "merchant_product_overrides"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "merchant_product_id",
            "field_name",
            name="uq_merchant_prod_override_field",
        ),
        Index("ix_merchant_prod_overrides_lookup", "merchant_id", "merchant_product_id"),
    )

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    merchant_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_products.id", ondelete="CASCADE"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    override_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    previous_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    merchant: Mapped[Merchant | None] = relationship(foreign_keys=[merchant_id])
    merchant_product: Mapped[MerchantProduct | None] = relationship(
        foreign_keys=[merchant_product_id]
    )
