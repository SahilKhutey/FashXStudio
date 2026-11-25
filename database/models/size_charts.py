"""SQLAlchemy models for Phase 08.1 Product Size Data, Revisions, and Availability."""

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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class SizeSystemDefinitionRecord(Base, UUIDPrimaryKeyMixin):
    """Registered sizing system definitions."""

    __tablename__ = "size_system_definitions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_size_system_code"),
        Index("ix_size_system_merchant", "merchant_id"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    system_type: Mapped[str] = mapped_column(String(32), nullable=False)
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="GENERAL")
    market: Mapped[str] = mapped_column(String(16), nullable=False, default="GLOBAL")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    mapping_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNMAPPED")
    labels_json: Mapped[list] = mapped_column(JSON, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MeasurementFieldDefinitionRecord(Base, UUIDPrimaryKeyMixin):
    """Registered garment-specific measurement fields and range constraints."""

    __tablename__ = "measurement_field_definitions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_measurement_field_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    allowed_categories_json: Mapped[list] = mapped_column(JSON, nullable=False)
    minimum_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    maximum_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProductSizeChartRecord(Base, UUIDPrimaryKeyMixin):
    """Product-level size chart container and active revision pointer."""

    __tablename__ = "product_size_charts"
    __table_args__ = (
        UniqueConstraint("merchant_product_id", name="uq_product_size_charts_product"),
        Index("ix_product_size_charts_merchant", "merchant_id"),
    )

    merchant_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_revision_id: Mapped[UUID | None] = mapped_column(nullable=True)
    chart_status: Mapped[str] = mapped_column(String(32), nullable=False, default="AVAILABLE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    revisions: Mapped[list[SizeChartRevisionRecord]] = relationship(
        back_populates="chart", cascade="all, delete-orphan"
    )


class SizeChartRevisionRecord(Base, UUIDPrimaryKeyMixin):
    """Immutable, versioned revision of a merchant size chart."""

    __tablename__ = "size_chart_revisions"
    __table_args__ = (
        UniqueConstraint("chart_id", "version", name="uq_size_chart_revision_version"),
        Index("ix_size_chart_revisions_product", "merchant_product_id"),
        Index("ix_size_chart_revisions_fingerprint", "content_fingerprint"),
    )

    chart_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_size_charts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    merchant_product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    size_system_code: Mapped[str] = mapped_column(String(64), nullable=False)
    measurement_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    default_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="CM")
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rows_json: Mapped[list] = mapped_column(JSON, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chart: Mapped[ProductSizeChartRecord] = relationship(back_populates="revisions")
    rows: Mapped[list[SizeChartRowRecord]] = relationship(
        back_populates="revision", cascade="all, delete-orphan"
    )


class SizeChartRowRecord(Base, UUIDPrimaryKeyMixin):
    """An individual size label row within an immutable chart revision."""

    __tablename__ = "size_chart_rows"
    __table_args__ = (
        UniqueConstraint("revision_id", "merchant_size", name="uq_size_chart_row_label"),
        Index("ix_size_chart_rows_revision", "revision_id"),
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("size_chart_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    merchant_size: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    revision: Mapped[SizeChartRevisionRecord] = relationship(back_populates="rows")
    measurements: Mapped[list[SizeChartMeasurementRecord]] = relationship(
        back_populates="row", cascade="all, delete-orphan"
    )


class SizeChartMeasurementRecord(Base, UUIDPrimaryKeyMixin):
    """A granular linear measurement attribute for a size row."""

    __tablename__ = "size_chart_measurements"
    __table_args__ = (
        UniqueConstraint("row_id", "field_code", name="uq_size_chart_row_field"),
        Index("ix_size_chart_measurements_row", "row_id"),
    )

    row_id: Mapped[UUID] = mapped_column(
        ForeignKey("size_chart_rows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_code: Mapped[str] = mapped_column(String(32), nullable=False)
    original_value: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    original_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    normalized_value: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    normalized_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="CM")

    row: Mapped[SizeChartRowRecord] = relationship(back_populates="measurements")


class InventorySnapshotRecord(Base, UUIDPrimaryKeyMixin):
    """Time-stamped audit observation of purchasable variant availability."""

    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        Index("ix_inventory_snapshots_variant", "variant_id"),
        Index("ix_inventory_snapshots_product", "merchant_product_id"),
        Index("ix_inventory_snapshots_observed", "observed_at"),
    )

    variant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    merchant_product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    colour_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SizeChartEventRecord(Base, UUIDPrimaryKeyMixin):
    """Audit log of lifecycle and version transitions for product size charts."""

    __tablename__ = "size_chart_events"
    __table_args__ = (
        Index("ix_size_chart_events_product", "merchant_product_id"),
        Index("ix_size_chart_events_chart", "chart_id"),
        Index("ix_size_chart_events_created", "created_at"),
    )

    chart_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    merchant_product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    change_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SizeChartQuarantineRecord(Base, UUIDPrimaryKeyMixin):
    """Quarantine log for rejected, invalid, or ambiguous chart submissions."""

    __tablename__ = "size_chart_quarantine"
    __table_args__ = (
        Index("ix_size_chart_quarantine_product", "merchant_product_id"),
        Index("ix_size_chart_quarantine_merchant", "merchant_id"),
        Index("ix_size_chart_quarantine_status", "review_status"),
    )

    merchant_product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    merchant_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    error_codes_json: Mapped[list] = mapped_column(JSON, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
