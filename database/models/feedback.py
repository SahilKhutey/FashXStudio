"""SQLAlchemy models for Phase 08.5 Feedback Loop events, projections, outbox, and consents."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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


class FeedbackEventRecord(Base, UUIDPrimaryKeyMixin):
    """Append-only event history for shopper feedback and interaction signals."""

    __tablename__ = "feedback_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_feedback_events_event_id"),
        Index("ix_feedback_events_user_occurred", "user_id", "occurred_at"),
        Index("ix_feedback_events_subject_occurred", "subject_type", "subject_id", "occurred_at"),
    )

    event_id: Mapped[UUID] = mapped_column(nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    feedback_class: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mobile")
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    context_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    consent_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")


class FeedbackProcessingRecord(Base):
    """Idempotent worker processing ledger for feedback events."""

    __tablename__ = "feedback_processing"

    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)


class FeedbackOutboxRecord(Base, UUIDPrimaryKeyMixin):
    """Transactional outbox record for durable async feedback processing."""

    __tablename__ = "feedback_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_feedback_outbox_event_id"),
        Index("ix_feedback_outbox_status_created", "status", "created_at"),
    )

    event_id: Mapped[UUID] = mapped_column(nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(64), nullable=False, default="feedback.events")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ShopperProductReactionRecord(Base, UUIDPrimaryKeyMixin):
    """Current like/dislike projection per authenticated shopper and product."""

    __tablename__ = "shopper_product_reactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_shopper_product_reactions_user_product",
        ),
        CheckConstraint(
            "reaction IN ('LIKE', 'DISLIKE', 'NONE')",
            name="ck_shopper_product_reaction_state",
        ),
        Index("ix_shopper_product_reactions_user", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reaction: Mapped[str] = mapped_column(String(20), nullable=False, default="NONE")
    source_event_id: Mapped[UUID] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ShopperSavedProductRecord(Base, UUIDPrimaryKeyMixin):
    """Current saved-product projection per authenticated shopper and product."""

    __tablename__ = "shopper_saved_products"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_shopper_saved_products_user_product",
        ),
        Index("ix_shopper_saved_products_user_saved", "user_id", "is_saved"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    merchant_offer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_event_id: Mapped[UUID] = mapped_column(nullable=False)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ShopperConsentRecord(Base, UUIDPrimaryKeyMixin):
    """Append-only purpose-specific consent history for feedback & personalization."""

    __tablename__ = "shopper_consent_records"
    __table_args__ = (
        Index("ix_shopper_consent_user_purpose", "user_id", "purpose", "recorded_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False, default="2026.1")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="app")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
