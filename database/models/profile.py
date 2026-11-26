from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


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
    tryon_photo_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_photos.id", ondelete="SET NULL")
    )
    skin_tone_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("skin_tone_results.id", ondelete="SET NULL")
    )
    ready_for_tryon: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ShopperProfile(Base, UUIDPrimaryKeyMixin):
    """Structured, editable, and extensible shopper fit and style profile."""

    __tablename__ = "shopper_profiles"
    __table_args__ = (
        CheckConstraint(
            "height_cm IS NULL OR (height_cm >= 80 AND height_cm <= 250)",
            name="ck_shopper_profiles_height",
        ),
        CheckConstraint(
            "weight_kg IS NULL OR (weight_kg >= 20 AND weight_kg <= 400)",
            name="ck_shopper_profiles_weight",
        ),
        CheckConstraint("version >= 1", name="ck_shopper_profiles_version"),
        Index("ix_shopper_profiles_updated_at", "updated_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    preferred_size_system: Mapped[str | None] = mapped_column(String(8), nullable=True)
    preferred_measurement_unit: Mapped[str] = mapped_column(
        String(8), default="CM", server_default="CM", nullable=False
    )
    preferred_fit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    style_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_colors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    product_categories: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    shopping_preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProfileCategorySize(Base, UUIDPrimaryKeyMixin):
    """Shopper declared size preferences for specific catalog categories."""

    __tablename__ = "profile_category_sizes"
    __table_args__ = (
        UniqueConstraint("user_id", "category_code", name="uq_profile_category_size"),
        Index("ix_profile_category_sizes_user", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    size_system: Mapped[str] = mapped_column(String(8), nullable=False)
    size_label: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProfileMeasurement(Base, UUIDPrimaryKeyMixin):
    """Shopper-controlled body measurements stored with explicit consent, basis, and versioning."""

    __tablename__ = "profile_measurements"
    __table_args__ = (
        CheckConstraint("value_cm > 0", name="ck_profile_measurements_value"),
        CheckConstraint("version >= 1", name="ck_profile_measurements_version"),
        UniqueConstraint("user_id", "measurement_type", name="uq_profile_measurements_user_type"),
        Index("ix_profile_measurements_user_type", "user_id", "measurement_type"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    measurement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    measurement_subject: Mapped[str] = mapped_column(
        String(16), default="BODY", server_default="BODY", nullable=False
    )
    value_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    original_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    original_unit: Mapped[str] = mapped_column(
        String(8), default="CM", server_default="CM", nullable=False
    )
    normalized_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    normalized_unit: Mapped[str] = mapped_column(
        String(8), default="CM", server_default="CM", nullable=False
    )
    source: Mapped[str] = mapped_column(String(24), default="MANUAL", nullable=False)
    measurement_method: Mapped[str] = mapped_column(
        String(32), default="SELF_MEASURED", server_default="SELF_MEASURED", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(24), default="PROVIDED", server_default="PROVIDED", nullable=False
    )
    validation_status: Mapped[str] = mapped_column(
        String(24), default="ACCEPTED", server_default="ACCEPTED", nullable=False
    )
    policy_version: Mapped[str] = mapped_column(
        String(20), default="1.0", server_default="1.0", nullable=False
    )
    schema_version: Mapped[str] = mapped_column(
        String(20), default="1.0", server_default="1.0", nullable=False
    )
    measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_record_id: Mapped[UUID | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class ProfileMeasurementHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail of changes to a shopper's body measurements."""

    __tablename__ = "profile_measurement_history"
    __table_args__ = (
        Index("ix_profile_meas_history_user_field", "user_id", "field_code"),
        Index("ix_profile_meas_history_changed", "changed_at"),
    )

    measurement_id: Mapped[UUID | None] = mapped_column(nullable=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    field_code: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    previous_unit: Mapped[str | None] = mapped_column(String(8), nullable=True)
    new_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    new_unit: Mapped[str | None] = mapped_column(String(8), nullable=True)
    normalized_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    change_source: Mapped[str] = mapped_column(String(32), default="SHOPPER_UPDATE", nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CategoryFitPreference(Base, UUIDPrimaryKeyMixin):
    """Shopper subjective fit style preference (SLIM, REGULAR, RELAXED, etc.) per garment category."""

    __tablename__ = "category_fit_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category", name="uq_category_fit_preferences_user_cat"),
        Index("ix_category_fit_preferences_user", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    fit_preference: Mapped[str] = mapped_column(String(24), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProfileAuditEvent(Base, UUIDPrimaryKeyMixin):
    """Sanitized security and privacy audit log for fit profile events (no PII measurement numbers)."""

    __tablename__ = "profile_audit_events"
    __table_args__ = (
        Index("ix_profile_audit_events_user", "user_id"),
        Index("ix_profile_audit_events_created", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
