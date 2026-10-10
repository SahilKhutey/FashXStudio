"""Feed impressions and signals (like, hide, not_interested) SQLAlchemy models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class FeedImpression(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "feed_impressions"
    __table_args__ = (
        Index("ix_impr_user_time", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    garment_id: Mapped[UUID] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    ranker_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FeedSignal(Base):
    __tablename__ = "feed_signals"
    __table_args__ = (
        CheckConstraint(
            "action IN ('like', 'hide', 'not_interested')",
            name="ck_feed_signal_action",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    garment_id: Mapped[UUID] = mapped_column(primary_key=True, nullable=False)
    action: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
