from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class WardrobeItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "wardrobe_items"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="RESTRICT"))
    offer_id: Mapped[UUID | None] = mapped_column(ForeignKey("merchant_offers.id", ondelete="SET NULL"))
    tryon_artifact_id: Mapped[UUID | None] = mapped_column(ForeignKey("tryon_artifacts.id", ondelete="SET NULL"))
    snapshot_title: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    snapshot_image_key: Mapped[str] = mapped_column(Text, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BuyClick(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "buy_clicks"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="RESTRICT"))
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("merchant_offers.id", ondelete="RESTRICT"))
    affiliate_network: Mapped[str | None] = mapped_column(String(64))
    tracking_id: Mapped[str | None] = mapped_column(String(255))
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FitFeedback(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "fit_feedback"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="RESTRICT"))
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("brands.id", ondelete="RESTRICT"))
    buy_click_id: Mapped[UUID | None] = mapped_column(ForeignKey("buy_clicks.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    fit_type: Mapped[str | None] = mapped_column(String(64))
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TryOnFeedback(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tryon_feedback"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tryon_job_id: Mapped[UUID] = mapped_column(ForeignKey("tryon_jobs.id", ondelete="CASCADE"))
    visual_accuracy: Mapped[str] = mapped_column(String(32), nullable=False)
    purchase_confidence: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "tryon_job_id", name="uq_tryon_feedback_user_job"),
    )


class FeedExclusion(Base):
    __tablename__ = "feed_exclusions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), primary_key=True)
    reason: Mapped[str] = mapped_column(String(64), default="rejected", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DomainEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "domain_events"

    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    schema_version: Mapped[int] = mapped_column(default=1, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    object_type: Mapped[str | None] = mapped_column(String(64))
    object_id: Mapped[UUID | None] = mapped_column()
    trace_id: Mapped[UUID | None] = mapped_column(index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
