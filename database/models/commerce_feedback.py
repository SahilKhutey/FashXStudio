from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class WardrobeItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "wardrobe_items"
    __table_args__ = (
        Index("ix_wardrobe_items_saved_at", "saved_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="RESTRICT")
    )
    offer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchant_offers.id", ondelete="SET NULL")
    )
    tryon_artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tryon_artifacts.id", ondelete="SET NULL")
    )
    snapshot_title: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    snapshot_image_key: Mapped[str] = mapped_column(Text, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BuyClick(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "buy_clicks"
    __table_args__ = (
        Index("ix_buy_clicks_clicked_at", "clicked_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="RESTRICT")
    )
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("merchant_offers.id", ondelete="RESTRICT"))
    affiliate_network: Mapped[str | None] = mapped_column(String(64))
    tracking_id: Mapped[str | None] = mapped_column(String(255))
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FitFeedback(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "fit_feedback"
    __table_args__ = (
        Index("ix_fit_feedback_brand_size", "brand_id", "category", "fit_type", "size_label"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="RESTRICT")
    )
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="RESTRICT"))
    buy_click_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buy_clicks.id", ondelete="SET NULL")
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    fit_type: Mapped[str | None] = mapped_column(String(64))
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TryOnFeedback(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "tryon_job_id", name="uq_tryon_feedback_user_job"),
        Index("ix_tryon_feedback_created_at", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tryon_job_id: Mapped[UUID] = mapped_column(ForeignKey("tryon_jobs.id", ondelete="CASCADE"))
    visual_accuracy: Mapped[str] = mapped_column(String(32), nullable=False)
    purchase_confidence: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeedExclusion(Base):
    __tablename__ = "feed_exclusions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), primary_key=True
    )
    reason: Mapped[str] = mapped_column(String(64), default="rejected", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DomainEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "domain_events"
    __table_args__ = (
        Index("ix_domain_events_event_type", "event_type", "occurred_at"),
        Index("ix_domain_events_user_id", "user_id", "occurred_at"),
        Index("ix_domain_events_type_occurred_user", "event_type", "occurred_at", "user_id"),
    )

    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[int] = mapped_column(default=1, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    object_type: Mapped[str | None] = mapped_column(String(64))
    object_id: Mapped[UUID | None] = mapped_column()
    trace_id: Mapped[UUID | None] = mapped_column(index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
