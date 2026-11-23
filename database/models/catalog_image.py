from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    pass


class ImageAssetStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETION_FAILED = "DELETION_FAILED"
    DELETED = "DELETED"
    REJECTED = "REJECTED"


class ImageTransformationType(StrEnum):
    DISPLAY_THUMBNAIL = "DISPLAY_THUMBNAIL"
    DISPLAY_CARD = "DISPLAY_CARD"
    DISPLAY_DETAIL = "DISPLAY_DETAIL"
    VTO_INPUT = "VTO_INPUT"
    OTHER_AUTHORIZED = "OTHER_AUTHORIZED"


class ImageTakedownScope(StrEnum):
    SOURCE = "SOURCE"
    MERCHANT = "MERCHANT"
    PRODUCT = "PRODUCT"
    ASSET = "ASSET"


class ImageTakedownStatus(StrEnum):
    RECEIVED = "RECEIVED"
    SUSPENDED = "SUSPENDED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXCEPTION = "EXCEPTION"


class ImageDeletionTargetType(StrEnum):
    ORIGINAL = "ORIGINAL"
    DISPLAY_DERIVATIVE = "DISPLAY_DERIVATIVE"
    VTO_DERIVATIVE = "VTO_DERIVATIVE"
    CACHE = "CACHE"
    EXTERNAL_PROCESSOR = "EXTERNAL_PROCESSOR"


class ImageDeletionJobStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CatalogImageAsset(Base, UUIDPrimaryKeyMixin):
    """Tracks the full provenance, rights, raw original, derivative transformations, and takedown lifecycle of a merchant product image."""

    __tablename__ = "catalog_image_assets"
    __table_args__ = (
        Index("ix_image_asset_source_product", "source_id", "source_product_id"),
        Index("ix_image_asset_original_hash", "original_sha256"),
        Index("ix_image_asset_normalized_hash", "normalized_sha256"),
        Index("ix_image_asset_status", "status"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    source_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_variant_id: Mapped[str | None] = mapped_column(String(255))
    source_reference: Mapped[str | None] = mapped_column(Text)
    source_reference_hash: Mapped[str | None] = mapped_column(String(64))

    original_storage_key: Mapped[str | None] = mapped_column(Text)
    original_sha256: Mapped[str | None] = mapped_column(String(64))
    normalized_sha256: Mapped[str | None] = mapped_column(String(64))
    perceptual_hash: Mapped[str | None] = mapped_column(String(255))

    original_mime_type: Mapped[str | None] = mapped_column(String(100))
    original_width: Mapped[int | None] = mapped_column(Integer)
    original_height: Mapped[int | None] = mapped_column(Integer)
    original_bytes: Mapped[int | None] = mapped_column(BigInteger)

    permission_evidence_id: Mapped[UUID | None] = mapped_column()
    permission_revision: Mapped[int | None] = mapped_column(Integer)
    permission_policy_version: Mapped[str | None] = mapped_column(String(64))

    status: Mapped[str] = mapped_column(
        String(32), default=ImageAssetStatus.PENDING.value, server_default="PENDING", nullable=False
    )
    quality_score: Mapped[str | None] = mapped_column(String(32))
    quality_notes: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    transformations: Mapped[list[CatalogImageTransformation]] = relationship(
        "CatalogImageTransformation", back_populates="asset", cascade="all, delete-orphan"
    )


class CatalogImageTransformation(Base, UUIDPrimaryKeyMixin):
    """Tracks reproducible, versioned derivative images (thumbnails, display cards, VTO inputs)."""

    __tablename__ = "catalog_image_transformations"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "transformation_type",
            "transformation_version",
            name="uq_asset_transformation_version",
        ),
        Index("ix_image_transformation_asset", "asset_id"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_image_assets.id", ondelete="CASCADE"), nullable=False
    )
    transformation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    processor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    processor_version: Mapped[str | None] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    output_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    output_width: Mapped[int] = mapped_column(Integer, nullable=False)
    output_height: Mapped[int] = mapped_column(Integer, nullable=False)
    output_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    output_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    asset: Mapped[CatalogImageAsset] = relationship(
        "CatalogImageAsset", back_populates="transformations"
    )


class CatalogImageTakedown(Base, UUIDPrimaryKeyMixin):
    """Records image takedown events and lifecycle completion state."""

    __tablename__ = "catalog_image_takedowns"
    __table_args__ = (
        Index("ix_catalog_image_takedown_source", "source_id"),
        Index("ix_catalog_image_takedown_status", "status"),
    )

    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="SET NULL")
    )
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL")
    )
    scope_type: Mapped[str] = mapped_column(
        String(32), default=ImageTakedownScope.SOURCE.value, server_default="SOURCE", nullable=False
    )
    scope_target: Mapped[str | None] = mapped_column(String(255))
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ImageTakedownStatus.RECEIVED.value, server_default="RECEIVED", nullable=False
    )
    audit_metadata: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CatalogImageDeletionJob(Base, UUIDPrimaryKeyMixin):
    """Durable tracking of per-object deletion targets across storage, CDN caches, and external processors."""

    __tablename__ = "catalog_image_deletion_jobs"
    __table_args__ = (
        Index("ix_image_deletion_job_takedown", "takedown_id"),
        Index("ix_image_deletion_job_asset", "asset_id"),
        Index("ix_image_deletion_job_status", "status"),
    )

    takedown_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_image_takedowns.id", ondelete="CASCADE")
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_image_assets.id", ondelete="CASCADE")
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(
        String(32), default=ImageDeletionTargetType.ORIGINAL.value, server_default="ORIGINAL", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ImageDeletionJobStatus.PENDING.value, server_default="PENDING", nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
