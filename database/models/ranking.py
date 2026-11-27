"""SQLAlchemy models for Phase 08.4 Personalized Product Ranking persistence."""

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


class ProductFeedbackRecord(Base, UUIDPrimaryKeyMixin):
    """Explicit shopper product feedback (like, dislike, save, not interested)."""

    __tablename__ = "product_feedback"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            "feedback_type",
            name="uq_product_feedback_user_product_type",
        ),
        Index("ix_product_feedback_user_created", "user_id", "created_at"),
        Index("ix_product_feedback_product_created", "product_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="api")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RankingPreferenceRecord(Base, UUIDPrimaryKeyMixin):
    """Versioned shopper ranking preferences (styles, colors, categories, budget)."""

    __tablename__ = "shopper_ranking_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_shopper_ranking_preferences_user"),
        Index("ix_shopper_ranking_preferences_user", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    style_preferences_json: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    preferred_colors_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    disliked_colors_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_categories_json: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class RankingEventRecord(Base, UUIDPrimaryKeyMixin):
    """Audit snapshot for personalized/baseline ranking requests."""

    __tablename__ = "ranking_events"
    __table_args__ = (
        Index("ix_ranking_events_version_created", "ranking_version", "created_at"),
        Index("ix_ranking_events_user_created", "user_id", "created_at"),
    )

    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ranking_version: Mapped[str] = mapped_column(String(32), nullable=False)
    config_version: Mapped[str] = mapped_column(String(32), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    experiment_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eligible_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    returned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    results_snapshot_json: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RankingEvaluationRunRecord(Base, UUIDPrimaryKeyMixin):
    """Offline evaluation comparison run (baseline vs personalized)."""

    __tablename__ = "ranking_evaluation_runs"
    __table_args__ = (
        Index("ix_ranking_eval_runs_dataset", "dataset_version"),
        Index("ix_ranking_eval_runs_created", "created_at"),
    )

    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    personalized_version: Mapped[str] = mapped_column(String(32), nullable=False)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    all_gates_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
