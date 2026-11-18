from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class CatalogSyncCheckpoint(Base, UUIDPrimaryKeyMixin):
    """Durable synchronization watermark and cursor tracking for catalog sources."""

    __tablename__ = "catalog_sync_checkpoints"
    __table_args__ = (
        UniqueConstraint("source_id", "checkpoint_type", name="uq_sync_checkpoint_source_type"),
        Index("ix_sync_checkpoint_source", "source_id"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    checkpoint_type: Mapped[str] = mapped_column(String(30), nullable=False)  # full | incremental
    cursor_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CatalogSyncRun(Base, UUIDPrimaryKeyMixin):
    """Historical and active sync run tracking with granular page and product metrics."""

    __tablename__ = "catalog_sync_runs"
    __table_args__ = (
        Index("ix_sync_runs_source", "source_id", "started_at"),
        Index("ix_sync_runs_status", "status"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # full | incremental
    status: Mapped[str] = mapped_column(
        String(30), default="running", server_default="running", nullable=False
    )  # running | completed | failed | aborted | recovering
    snapshot_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pages_fetched: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    products_seen: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    products_inserted: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    products_updated: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    products_rejected: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
