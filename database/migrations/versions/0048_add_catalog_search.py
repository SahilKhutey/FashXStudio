"""Add catalog search documents, text embeddings, sessions, events and synonyms

Revision ID: 0048_add_catalog_search
Revises: 0047_add_image_embeddings
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from database.models.base import Vector512

revision: str = "0048_add_catalog_search"
down_revision: str | None = "0047_add_image_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 1. Create product_search_documents
    op.create_table(
        "product_search_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_product_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("subcategory_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("search_document", sa.Text(), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("enrichment_version", sa.String(length=32), nullable=True),
        sa.Column("source_revision", sa.String(length=64), nullable=True),
        sa.Column(
            "indexed_attributes_json",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["merchant_product_id"],
            ["merchant_products.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["brand_id"],
            ["brands.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_product_id", name="uq_search_doc_merchant_product"),
    )
    op.create_index("ix_search_document_category", "product_search_documents", ["category_id"])
    op.create_index("ix_search_document_brand", "product_search_documents", ["brand_id"])
    op.create_index("ix_search_document_product", "product_search_documents", ["product_id"])
    op.create_index("ix_search_document_merchant", "product_search_documents", ["merchant_id"])

    # 2. Create product_text_embeddings
    op.create_table(
        "product_text_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_product_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("text_revision_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="512"),
        sa.Column("embedding", Vector512(512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="READY"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["merchant_product_id"],
            ["merchant_products.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_text_embedding_merchant_product", "product_text_embeddings", ["merchant_product_id"]
    )
    op.create_index(
        "ix_text_embedding_model", "product_text_embeddings", ["model_id", "model_version"]
    )
    op.create_index("ix_text_embedding_status", "product_text_embeddings", ["status"])

    if is_pg:
        op.execute(
            """
            CREATE INDEX idx_product_text_embeddings_hnsw
            ON product_text_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )

    # 3. Create search_sessions
    op.create_table(
        "search_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("session_token", sa.String(length=128), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=True),
        sa.Column("applied_filters_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("sort_order", sa.String(length=32), nullable=False, server_default="relevance"),
        sa.Column("result_ids_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("total_results", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token", name="uq_search_sessions_token"),
    )
    op.create_index("ix_search_sessions_token", "search_sessions", ["session_token"])
    op.create_index("ix_search_sessions_user", "search_sessions", ["user_id"])

    # 4. Create product_search_events
    op.create_table(
        "product_search_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("filter_key", sa.String(length=64), nullable=True),
        sa.Column("filter_value", sa.Text(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("merchant_product_id", sa.Uuid(), nullable=True),
        sa.Column("rank_position", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["search_sessions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_events_type", "product_search_events", ["event_type"])
    op.create_index("ix_search_events_session", "product_search_events", ["session_id"])
    op.create_index("ix_search_events_user", "product_search_events", ["user_id"])

    # 5. Create search_synonyms
    op.create_table(
        "search_synonyms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("term", sa.String(length=100), nullable=False),
        sa.Column("synonym", sa.String(length=100), nullable=False),
        sa.Column("category_scope", sa.String(length=64), nullable=True),
        sa.Column("is_bidirectional", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_synonyms_term", "search_synonyms", ["term"])

    # Pre-seed initial fashion synonyms
    op.execute(
        sa.text(
            """
            INSERT INTO search_synonyms (id, term, synonym, category_scope, is_bidirectional)
            VALUES 
                ('d1e1f1a1-0000-0000-0000-000000000001', 'tee', 't-shirt', 'tops', true),
                ('d1e1f1a1-0000-0000-0000-000000000002', 'kurti', 'short kurta', 'indian_wear', true),
                ('d1e1f1a1-0000-0000-0000-000000000003', 'denim', 'jeans', 'bottoms', true)
            """
        )
    )

    # 6. Create search_evaluation_runs
    op.create_table(
        "search_evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_version", sa.String(length=32), nullable=False),
        sa.Column("dataset_size", sa.Integer(), nullable=False),
        sa.Column("precision_at_10", sa.Float(), nullable=False),
        sa.Column("recall_at_10", sa.Float(), nullable=False),
        sa.Column("mrr", sa.Float(), nullable=False),
        sa.Column("ndcg_at_10", sa.Float(), nullable=False),
        sa.Column("zero_result_rate", sa.Float(), nullable=False),
        sa.Column("hard_filter_violation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("takedown_violation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("search_evaluation_runs")
    op.drop_table("search_synonyms")
    op.drop_table("product_search_events")
    op.drop_table("search_sessions")
    op.drop_table("product_text_embeddings")
    op.drop_table("product_search_documents")
