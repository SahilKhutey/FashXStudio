from __future__ import annotations

from datetime import datetime
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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin
from .catalog import MerchantOffer


class CatalogEvaluationRun(Base, UUIDPrimaryKeyMixin):
    """Historical record of an automated catalog target measurement and release gate evaluation."""

    __tablename__ = "catalog_evaluation_runs"
    __table_args__ = (
        Index("ix_catalog_eval_runs_created", "created_at"),
        Index("ix_catalog_eval_runs_status", "status"),
    )

    configuration_version: Mapped[str] = mapped_column(
        String(32), default="1.0", server_default="1.0", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="COMPLETED", server_default="COMPLETED", nullable=False
    )
    all_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    metrics_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    detailed_report: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CatalogLinkHealthCheck(Base, UUIDPrimaryKeyMixin):
    """Observation log of a validated merchant destination link with SSRF safety results."""

    __tablename__ = "catalog_link_health_checks"
    __table_args__ = (
        Index("ix_link_health_offer", "offer_id"),
        Index("ix_link_health_status", "status"),
        Index("ix_link_health_checked", "checked_at"),
    )

    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_offers.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="UNVERIFIED", server_default="UNVERIFIED", nullable=False
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    offer: Mapped[MerchantOffer] = relationship(foreign_keys=[offer_id])
