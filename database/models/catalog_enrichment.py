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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class ProductEnrichmentRunRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_enrichment_runs"

    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    source_revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    enrichment_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="QUEUED", server_default="QUEUED", nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    results: Mapped[list[ProductEnrichmentResultRecord]] = relationship(
        back_populates="run_record", cascade="all, delete-orphan"
    )
    model_runs: Mapped[list[ProductEnrichmentModelRunRecord]] = relationship(
        back_populates="run_record", cascade="all, delete-orphan"
    )


class ProductEnrichmentResultRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_enrichment_results"

    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_enrichment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    enrichment_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    garment_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_product_enrichment_current", "product_id", "is_current"),
    )

    run_record: Mapped[ProductEnrichmentRunRecord] = relationship(back_populates="results")


class ProductAttributeEvidenceRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_attribute_evidence"

    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    attribute_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_product_attr_evidence_lookup", "product_id", "attribute_id"),
    )


class ProductAttributeReviewRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_attribute_reviews"

    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    merchant_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    attribute_id: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", server_default="PENDING", nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    flags_json: Mapped[list] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_product_attr_reviews_tenant", "merchant_id", "status"),
    )

    events: Mapped[list[ProductAttributeReviewEventRecord]] = relationship(
        back_populates="review_record", cascade="all, delete-orphan"
    )


class ProductAttributeReviewEventRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_attribute_review_events"

    review_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_attribute_reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    review_record: Mapped[ProductAttributeReviewRecord] = relationship(back_populates="events")


class ProductEnrichmentModelRunRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_enrichment_model_runs"

    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_enrichment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run_record: Mapped[ProductEnrichmentRunRecord] = relationship(back_populates="model_runs")
