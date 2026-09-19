"""
SQLAlchemy 2.x Declarative Persistence Models
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    consent: Mapped[Optional["UserConsentModel"]] = relationship(
        "UserConsentModel", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tryon_jobs: Mapped[list["TryOnJobModel"]] = relationship(
        "TryOnJobModel", back_populates="user", cascade="all, delete-orphan"
    )


class UserConsentModel(Base):
    __tablename__ = "user_consents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    body_photo_processing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    measurement_extraction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    camera_stream_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    personalization_profiling: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ml_model_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    third_party_analytics: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="consent")


class CanonicalGarmentModel(Base):
    __tablename__ = "canonical_garments"

    canonical_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subcategory: Mapped[str] = mapped_column(String(50), nullable=False)
    gender_target: Mapped[str] = mapped_column(String(20), nullable=False)
    silhouette: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(50), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    color_palette_type: Mapped[str] = mapped_column(String(50), nullable=False)
    material: Mapped[str] = mapped_column(String(100), nullable=False)
    formality_level: Mapped[str] = mapped_column(String(50), default="casual", nullable=False)
    enrichment_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    garment_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TryOnJobModel(Base):
    __tablename__ = "tryon_jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    canonical_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_garments.canonical_id", ondelete="CASCADE"), nullable=False
    )
    user_photo_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False, index=True)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    result_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    queue_wait_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    inference_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="tryon_jobs")
