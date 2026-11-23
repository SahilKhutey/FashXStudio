from __future__ import annotations

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin, Vector512


class ProductSearchDocumentRecord(Base, UUIDPrimaryKeyMixin):
    """Normalized search documents for merchant products."""

    __tablename__ = "product_search_documents"
    __table_args__ = (
        UniqueConstraint("merchant_product_id", name="uq_search_doc_merchant_product"),
        Index("ix_search_document_category", "category_id"),
        Index("ix_search_document_brand", "brand_id"),
        Index("ix_search_document_product", "product_id"),
        Index("ix_search_document_merchant", "merchant_id"),
    )

    merchant_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_products.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(nullable=False)
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[UUID | None] = mapped_column(nullable=True)
    subcategory_id: Mapped[UUID | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_document: Mapped[str] = mapped_column(Text, nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    enrichment_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    indexed_attributes_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProductTextEmbeddingRecord(Base, UUIDPrimaryKeyMixin):
    """Semantic multimodal text embeddings for catalog listings."""

    __tablename__ = "product_text_embeddings"
    __table_args__ = (
        Index("ix_text_embedding_merchant_product", "merchant_product_id"),
        Index("ix_text_embedding_model", "model_id", "model_version"),
        Index("ix_text_embedding_status", "status"),
        Index(
            "idx_product_text_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    merchant_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_products.id", ondelete="CASCADE"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    text_revision_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=512, server_default="512", nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector512(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="READY", server_default="READY", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SearchSessionRecord(Base, UUIDPrimaryKeyMixin):
    """Search sessions for stable cursor pagination and snapshot consistency."""

    __tablename__ = "search_sessions"
    __table_args__ = (
        UniqueConstraint("session_token", name="uq_search_sessions_token"),
        Index("ix_search_sessions_token", "session_token"),
        Index("ix_search_sessions_user", "user_id"),
    )

    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    session_token: Mapped[str] = mapped_column(String(128), nullable=False)
    query_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_filters_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    sort_order: Mapped[str] = mapped_column(
        String(32), default="relevance", server_default="relevance", nullable=False
    )
    result_ids_json: Mapped[list] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    total_results: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    events: Mapped[list[ProductSearchEventRecord]] = relationship(
        "ProductSearchEventRecord", back_populates="session", cascade="all, delete-orphan"
    )


class ProductSearchEventRecord(Base, UUIDPrimaryKeyMixin):
    """Interaction events for search queries, clicks, saves, and handoffs."""

    __tablename__ = "product_search_events"
    __table_args__ = (
        Index("ix_search_events_type", "event_type"),
        Index("ix_search_events_session", "session_id"),
        Index("ix_search_events_user", "user_id"),
    )

    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("search_sessions.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    filter_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filter_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[UUID | None] = mapped_column(nullable=True)
    merchant_product_id: Mapped[UUID | None] = mapped_column(nullable=True)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SearchSessionRecord | None] = relationship(
        "SearchSessionRecord", back_populates="events"
    )


class SearchSynonymRecord(Base, UUIDPrimaryKeyMixin):
    """Controlled query synonyms and colloquial aliases."""

    __tablename__ = "search_synonyms"

    term: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    synonym: Mapped[str] = mapped_column(String(100), nullable=False)
    category_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_bidirectional: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )


class SearchEvaluationRunRecord(Base, UUIDPrimaryKeyMixin):
    """Relevance evaluation benchmarks, MRR, NDCG, and violation tracking."""

    __tablename__ = "search_evaluation_runs"

    evaluator_version: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    precision_at_10: Mapped[float] = mapped_column(Float, nullable=False)
    recall_at_10: Mapped[float] = mapped_column(Float, nullable=False)
    mrr: Mapped[float] = mapped_column(Float, nullable=False)
    ndcg_at_10: Mapped[float] = mapped_column(Float, nullable=False)
    zero_result_rate: Mapped[float] = mapped_column(Float, nullable=False)
    hard_filter_violation_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    takedown_violation_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    results_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = [
    "ProductSearchDocumentRecord",
    "ProductSearchEventRecord",
    "ProductTextEmbeddingRecord",
    "SearchEvaluationRunRecord",
    "SearchSessionRecord",
    "SearchSynonymRecord",
]
