from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
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

from .base import Base, UUIDPrimaryKeyMixin, Vector512


class EmbeddingModelRegistryRecord(Base):
    """Registry of models approved for catalog image embeddings."""

    __tablename__ = "embedding_model_registry"

    model_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_version: Mapped[str] = mapped_column(String(32), primary_key=True)
    dimension: Mapped[int] = mapped_column(Integer, default=512, server_default="512", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="APPROVED", server_default="APPROVED", nullable=False
    )
    architecture: Mapped[str] = mapped_column(String(64), nullable=False)
    framework: Mapped[str] = mapped_column(String(32), nullable=False)
    weights_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProductImageEmbeddingRecord(Base, UUIDPrimaryKeyMixin):
    """Persisted vector embeddings for catalog image assets."""

    __tablename__ = "product_image_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "image_asset_id", "model_id", "model_version", name="uq_image_embedding_asset_model"
        ),
        Index("ix_image_embedding_lookup", "product_id", "is_active"),
        Index("ix_image_embedding_active_search", "is_active", "model_id", "model_version"),
        Index("ix_image_embedding_sha256", "image_sha256"),
        Index(
            "idx_product_image_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    image_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_image_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector512(512), nullable=False)
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EmbeddingBatchRecord(Base, UUIDPrimaryKeyMixin):
    """Tracks asynchronous bulk embedding batches."""

    __tablename__ = "embedding_batches"
    __table_args__ = (
        UniqueConstraint("batch_key", name="uq_embedding_batches_key"),
        Index("ix_embedding_batches_key", "batch_key"),
    )

    batch_key: Mapped[str] = mapped_column(String(128), nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    succeeded_items: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", server_default="PENDING", nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    jobs: Mapped[list[EmbeddingJobRecord]] = relationship(
        "EmbeddingJobRecord", back_populates="batch", cascade="all, delete-orphan"
    )


class EmbeddingJobRecord(Base, UUIDPrimaryKeyMixin):
    """Tracks embedding execution state for individual image assets."""

    __tablename__ = "embedding_jobs"

    batch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("embedding_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    image_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_image_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", server_default="PENDING", nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    batch: Mapped[EmbeddingBatchRecord | None] = relationship(
        "EmbeddingBatchRecord", back_populates="jobs"
    )


class EmbeddingMigrationRecord(Base, UUIDPrimaryKeyMixin):
    """Tracks blue/green model migration cutover lifecycle."""

    __tablename__ = "embedding_migrations"

    source_model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    target_model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    migration_phase: Mapped[str] = mapped_column(
        String(32), default="PREPARATION", server_default="PREPARATION", nullable=False
    )
    total_records: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    migrated_records: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="IN_PROGRESS", server_default="IN_PROGRESS", nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
