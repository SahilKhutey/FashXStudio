from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class PilotInvite(Base):
    __tablename__ = "pilot_invites"

    code_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    cohort: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)  # campus | community | referral | other
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PilotParticipant(Base):
    __tablename__ = "pilot_participants"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    cohort: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    os: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_version: Mapped[str | None] = mapped_column(Text, nullable=True)


class PilotSurveyResponse(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "pilot_survey_responses"
    __table_args__ = (
        UniqueConstraint("user_id", "survey_key", name="uq_survey_once"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    survey_key: Mapped[str] = mapped_column(Text, nullable=False)
    answers: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PilotFeedback(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "pilot_feedback"
    __table_args__ = (
        CheckConstraint(
            "kind in ('bug','idea','praise','privacy')",
            name="ck_feedback_kind",
        ),
        CheckConstraint(
            "length(message) <= 2000",
            name="ck_feedback_len",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
