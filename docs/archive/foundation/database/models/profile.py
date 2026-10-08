from uuid import UUID

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin, Vector512


class BodyProfile(Base):
    __tablename__ = "body_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    build: Mapped[str | None] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float)
    pose_score: Mapped[float | None] = mapped_column(Float)
    framing_score: Mapped[float | None] = mapped_column(Float)
    landmark_confidence: Mapped[float | None] = mapped_column(Float)
    ready_for_tryon: Mapped[bool | None] = mapped_column(Boolean)
    quality_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    pose_provider: Mapped[str | None] = mapped_column(String(64))
    pose_provider_version: Mapped[str | None] = mapped_column(String(64))


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

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    colors_favored: Mapped[list[str]] = mapped_column(JSON, default=list)
    colors_avoided: Mapped[list[str]] = mapped_column(JSON, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)


class UserStyleProfile(Base):
    __tablename__ = "user_style_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector512(512), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)


class ProfileArtifact(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "profile_artifacts"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    body_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    preferences_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    tryon_photo_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_photos.id", ondelete="SET NULL"))
    skin_tone_result_id: Mapped[UUID | None] = mapped_column(ForeignKey("skin_tone_results.id", ondelete="SET NULL"))
    ready_for_tryon: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "version", name="uq_profile_artifacts_user_version"),)


class SkinToneResult(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skin_tone_results"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    photo_id: Mapped[UUID] = mapped_column(ForeignKey("user_photos.id", ondelete="CASCADE"), unique=True, nullable=False)
    ita_degrees: Mapped[float | None] = mapped_column(Float)
    tone_class: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
