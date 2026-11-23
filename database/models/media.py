from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
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


class MediaObject(Base, UUIDPrimaryKeyMixin):
    """Metadata repository for objects stored in private cloud storage (Rule I06)."""

    __tablename__ = "media_objects"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "kind in ('reference_photo', 'tryon_result', 'garment_render')",
            name="ck_media_kind",
        ),
        Index("ix_media_user_kind", "user_id", "kind"),
    )


class UserMedia(Base, UUIDPrimaryKeyMixin):
    """Metadata repository for validated user personal media (Phase 04.5)."""

    __tablename__ = "user_media"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_original: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sha256_normalized: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="user_media_size_positive"),
        CheckConstraint("width > 0", name="user_media_width_positive"),
        CheckConstraint("height > 0", name="user_media_height_positive"),
        CheckConstraint(
            "purpose in ('PROFILE_PHOTO', 'VTO_PERSONAL_PHOTO')",
            name="user_media_purpose_check",
        ),
        CheckConstraint(
            "status in ('AVAILABLE', 'DELETION_PENDING', 'DELETED', 'QUARANTINED')",
            name="user_media_status_check",
        ),
        UniqueConstraint("storage_bucket", "storage_key", name="uq_user_media_storage_key"),
        Index("idx_user_media_owner", "user_id", "created_at"),
        Index("idx_user_media_status", "status", "updated_at"),
    )


class MediaUpload(Base, UUIDPrimaryKeyMixin):
    """Tracks upload intent, presigned URL lifecycle, and validation state (Phase 04.5)."""

    __tablename__ = "media_uploads"

    image_id: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    quarantine_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    final_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    declared_content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    declared_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    min_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "declared_size_bytes > 0 AND min_size_bytes > 0 AND max_size_bytes >= min_size_bytes",
            name="media_upload_size_check",
        ),
        CheckConstraint(
            "status in ('PENDING_UPLOAD', 'VALIDATING', 'AVAILABLE', 'REJECTED', 'FAILED', 'EXPIRED', 'CANCELLED')",
            name="media_upload_status_check",
        ),
        Index("idx_media_uploads_expiry", "status", "expires_at"),
        Index("idx_media_uploads_user", "user_id", "created_at"),
    )
