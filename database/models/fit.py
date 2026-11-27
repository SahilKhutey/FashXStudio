"""SQLAlchemy models for Phase 08.3 Fit Recommendation evidence, candidates, and evaluation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class FitRecommendationEvidenceRecord(Base, UUIDPrimaryKeyMixin):
    """Immutable evidence reference attached to a persisted fit recommendation snapshot."""

    __tablename__ = "fit_recommendation_evidence"
    __table_args__ = (
        Index("ix_fit_rec_evidence_rec", "recommendation_id"),
        Index("ix_fit_rec_evidence_source", "source_type", "source_id"),
    )

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("fit_recommendations.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    measurement_basis: Mapped[str | None] = mapped_column(String(16), nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FitRecommendationCandidateRecord(Base, UUIDPrimaryKeyMixin):
    """Per-variant evaluation result recorded for reproducibility and audit."""

    __tablename__ = "fit_recommendation_candidates"
    __table_args__ = (Index("ix_fit_rec_candidates_rec", "recommendation_id"),)

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("fit_recommendations.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    merchant_size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mismatched_fields_json: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FitEvaluationCaseRecord(Base, UUIDPrimaryKeyMixin):
    """Versioned manually labelled ground-truth evaluation case (Phase 08.3 - Task 8.3.10)."""

    __tablename__ = "fit_evaluation_cases"
    __table_args__ = (
        UniqueConstraint("dataset_version", "case_key", name="uq_fit_eval_case_version_key"),
        Index("ix_fit_eval_cases_dataset", "dataset_version", "split_name"),
        Index("ix_fit_eval_cases_merchant", "merchant_id"),
    )

    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    case_key: Mapped[str] = mapped_column(String(128), nullable=False)
    split_name: Mapped[str] = mapped_column(String(24), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    merchant_offer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    variant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_chart_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    measurement_basis: Mapped[str] = mapped_column(String(16), nullable=False)
    shopper_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    expected_label: Mapped[str] = mapped_column(String(40), nullable=False)
    expected_size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acceptable_sizes_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    labelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FitEvaluationRunRecord(Base, UUIDPrimaryKeyMixin):
    """Reproducible evaluation run metrics and release gate results (Phase 08.3 - Task 8.3.11)."""

    __tablename__ = "fit_evaluation_runs"
    __table_args__ = (
        Index("ix_fit_eval_runs_dataset", "dataset_version"),
        Index("ix_fit_eval_runs_created", "created_at"),
    )

    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    fit_algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    category_policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_count: Mapped[int] = mapped_column(Integer, nullable=False)
    abstention_count: Mapped[int] = mapped_column(Integer, nullable=False)
    exact_size_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    acceptable_size_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    coverage: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    abstention_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    false_recommendation_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    gate_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
