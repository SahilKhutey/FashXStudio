from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin, Vector512


class BodyProfile(Base):
    __tablename__ = "body_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    build: Mapped[str | None] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(default=1, nullable=False)


class UserMeasurement(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_measurements"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    measurement: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    colors_favored: Mapped[list[str]] = mapped_column(JSON, default=list)
    colors_avoided: Mapped[list[str]] = mapped_column(JSON, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)


class OnboardingProfile(Base):
    """Mutable F02 context; identity remains owned by the Core User aggregate."""

    __tablename__ = "onboarding_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(512))
    region: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="not_started", nullable=False)
    step: Mapped[str] = mapped_column(String(32), default="basic", nullable=False)
    styles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    occasions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    fit_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    shopping_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    discovery_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserStyleProfile(Base):
    __tablename__ = "user_style_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector512(512))
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)


class ProfilePhotoJob(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "profile_photo_jobs"
    __table_args__ = (
        Index("ix_profile_photo_jobs_user_id", "user_id", "created_at"),
        Index("ix_profile_photo_jobs_status", "status", "created_at"),
    )

    photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_photos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SkinToneResult(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skin_tone_results"
    __table_args__ = (
        UniqueConstraint("photo_id", name="uq_skin_tone_results_photo"),
        Index("ix_skin_tone_results_user_id", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_photos.id", ondelete="CASCADE"), nullable=False
    )
    ita_degrees: Mapped[float | None] = mapped_column(Float)
    tone_class: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProfileArtifact(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "profile_artifacts"
    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_profile_artifacts_user_version"),
        Index("ix_profile_artifacts_user_id", "user_id", "version"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    body_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    preferences_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    tryon_photo_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_photos.id", ondelete="SET NULL"))
    skin_tone_result_id: Mapped[UUID | None] = mapped_column(ForeignKey("skin_tone_results.id", ondelete="SET NULL"))
    ready_for_tryon: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

