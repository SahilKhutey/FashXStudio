"""Add catalog image embeddings, model registry, batch tracking and migrations

Revision ID: 0047_add_image_embeddings
Revises: 0046_add_catalog_enrichment
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from database.models.base import Vector512

revision: str = "0047_add_image_embeddings"
down_revision: str | None = "0046_add_catalog_enrichment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Ensure pgvector extension on PostgreSQL
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. Create embedding_model_registry
    op.create_table(
        "embedding_model_registry",
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False, server_default="512"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="APPROVED"),
        sa.Column("architecture", sa.String(length=64), nullable=False),
        sa.Column("framework", sa.String(length=32), nullable=False),
        sa.Column("weights_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("model_id", "model_version"),
    )

    # Seed baseline approved OpenCLIP model
    op.execute(
        sa.text(
            """
            INSERT INTO embedding_model_registry (model_id, model_version, dimension, status, architecture, framework, metadata_json, registered_at)
            VALUES ('openclip_vit_b32', 'v1', 512, 'APPROVED', 'ViT-B/32', 'openclip', '{}', CURRENT_TIMESTAMP)
            """
        )
    )

    # 2. Create product_image_embeddings
    op.create_table(
        "product_image_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("image_asset_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("embedding", Vector512(512), nullable=False),
        sa.Column("image_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["image_asset_id"],
            ["catalog_image_assets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "image_asset_id", "model_id", "model_version", name="uq_image_embedding_asset_model"
        ),
    )
    op.create_index(
        "ix_product_image_embeddings_image_asset_id",
        "product_image_embeddings",
        ["image_asset_id"],
    )
    op.create_index(
        "ix_product_image_embeddings_product_id",
        "product_image_embeddings",
        ["product_id"],
    )
    op.create_index(
        "ix_product_image_embeddings_merchant_id",
        "product_image_embeddings",
        ["merchant_id"],
    )
    op.create_index(
        "ix_product_image_embeddings_model_id",
        "product_image_embeddings",
        ["model_id"],
    )
    op.create_index(
        "ix_product_image_embeddings_is_active",
        "product_image_embeddings",
        ["is_active"],
    )
    op.create_index(
        "ix_image_embedding_lookup",
        "product_image_embeddings",
        ["product_id", "is_active"],
    )
    op.create_index(
        "ix_image_embedding_active_search",
        "product_image_embeddings",
        ["is_active", "model_id", "model_version"],
    )
    op.create_index(
        "ix_image_embedding_sha256",
        "product_image_embeddings",
        ["image_sha256"],
    )

    if is_pg:
        op.execute(
            """
            CREATE INDEX idx_product_image_embeddings_hnsw
            ON product_image_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )

    # 3. Create embedding_batches
    op.create_table(
        "embedding_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_key", sa.String(length=128), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_key", name="uq_embedding_batches_key"),
    )
    op.create_index("ix_embedding_batches_key", "embedding_batches", ["batch_key"])

    # 4. Create embedding_jobs
    op.create_table(
        "embedding_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("image_asset_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["embedding_batches.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["image_asset_id"],
            ["catalog_image_assets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_embedding_jobs_batch_id", "embedding_jobs", ["batch_id"])
    op.create_index("ix_embedding_jobs_image_asset_id", "embedding_jobs", ["image_asset_id"])

    # 5. Create embedding_migrations
    op.create_table(
        "embedding_migrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_model_id", sa.String(length=64), nullable=False),
        sa.Column("source_model_version", sa.String(length=32), nullable=False),
        sa.Column("target_model_id", sa.String(length=64), nullable=False),
        sa.Column("target_model_version", sa.String(length=32), nullable=False),
        sa.Column("migration_phase", sa.String(length=32), nullable=False, server_default="PREPARATION"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("migrated_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="IN_PROGRESS"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("embedding_migrations")
    op.drop_table("embedding_jobs")
    op.drop_table("embedding_batches")
    op.drop_table("product_image_embeddings")
    op.drop_table("embedding_model_registry")
