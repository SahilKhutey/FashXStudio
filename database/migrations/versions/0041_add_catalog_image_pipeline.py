"""Add catalog image assets, transformations, takedowns, and deletion jobs

Revision ID: 0041_add_catalog_image_pipeline
Revises: 0040_add_catalog_ingestion_quarantine
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041_add_catalog_image_pipeline"
down_revision: str | None = "0040_add_catalog_ingestion_quarantine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create catalog_image_assets table
    op.create_table(
        "catalog_image_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_product_id", sa.String(length=255), nullable=False),
        sa.Column("source_variant_id", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("source_reference_hash", sa.String(length=64), nullable=True),
        sa.Column("original_storage_key", sa.Text(), nullable=True),
        sa.Column("original_sha256", sa.String(length=64), nullable=True),
        sa.Column("normalized_sha256", sa.String(length=64), nullable=True),
        sa.Column("perceptual_hash", sa.String(length=255), nullable=True),
        sa.Column("original_mime_type", sa.String(length=100), nullable=True),
        sa.Column("original_width", sa.Integer(), nullable=True),
        sa.Column("original_height", sa.Integer(), nullable=True),
        sa.Column("original_bytes", sa.BigInteger(), nullable=True),
        sa.Column("permission_evidence_id", sa.Uuid(), nullable=True),
        sa.Column("permission_revision", sa.Integer(), nullable=True),
        sa.Column("permission_policy_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("quality_score", sa.String(length=32), nullable=True),
        sa.Column("quality_notes", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_image_asset_source_product",
        "catalog_image_assets",
        ["source_id", "source_product_id"],
    )
    op.create_index(
        "ix_image_asset_original_hash",
        "catalog_image_assets",
        ["original_sha256"],
    )
    op.create_index(
        "ix_image_asset_normalized_hash",
        "catalog_image_assets",
        ["normalized_sha256"],
    )
    op.create_index(
        "ix_image_asset_status",
        "catalog_image_assets",
        ["status"],
    )

    # 2. Create catalog_image_transformations table
    op.create_table(
        "catalog_image_transformations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "asset_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_image_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transformation_type", sa.String(length=32), nullable=False),
        sa.Column("transformation_version", sa.String(length=64), nullable=False),
        sa.Column("processor_name", sa.String(length=100), nullable=False),
        sa.Column("processor_version", sa.String(length=100), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("output_mime_type", sa.String(length=100), nullable=False),
        sa.Column("output_width", sa.Integer(), nullable=False),
        sa.Column("output_height", sa.Integer(), nullable=False),
        sa.Column("output_bytes", sa.BigInteger(), nullable=False),
        sa.Column("output_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "asset_id",
            "transformation_type",
            "transformation_version",
            name="uq_asset_transformation_version",
        ),
    )
    op.create_index(
        "ix_image_transformation_asset",
        "catalog_image_transformations",
        ["asset_id"],
    )

    # 3. Create catalog_image_takedowns table
    op.create_table(
        "catalog_image_takedowns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scope_type", sa.String(length=32), nullable=False, server_default="SOURCE"),
        sa.Column("scope_target", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RECEIVED"),
        sa.Column("audit_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_catalog_image_takedown_source",
        "catalog_image_takedowns",
        ["source_id"],
    )
    op.create_index(
        "ix_catalog_image_takedown_status",
        "catalog_image_takedowns",
        ["status"],
    )

    # 4. Create catalog_image_deletion_jobs table
    op.create_table(
        "catalog_image_deletion_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "takedown_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_image_takedowns.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "asset_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_image_assets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False, server_default="ORIGINAL"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_image_deletion_job_takedown",
        "catalog_image_deletion_jobs",
        ["takedown_id"],
    )
    op.create_index(
        "ix_image_deletion_job_asset",
        "catalog_image_deletion_jobs",
        ["asset_id"],
    )
    op.create_index(
        "ix_image_deletion_job_status",
        "catalog_image_deletion_jobs",
        ["status"],
    )

    # 5. Add asset_id foreign key column to garment_images
    op.add_column(
        "garment_images",
        sa.Column(
            "asset_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_image_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_garment_images_asset_id",
        "garment_images",
        ["asset_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_garment_images_asset_id", table_name="garment_images")
    op.drop_column("garment_images", "asset_id")

    op.drop_index("ix_image_deletion_job_status", table_name="catalog_image_deletion_jobs")
    op.drop_index("ix_image_deletion_job_asset", table_name="catalog_image_deletion_jobs")
    op.drop_index("ix_image_deletion_job_takedown", table_name="catalog_image_deletion_jobs")
    op.drop_table("catalog_image_deletion_jobs")

    op.drop_index("ix_catalog_image_takedown_status", table_name="catalog_image_takedowns")
    op.drop_index("ix_catalog_image_takedown_source", table_name="catalog_image_takedowns")
    op.drop_table("catalog_image_takedowns")

    op.drop_index("ix_image_transformation_asset", table_name="catalog_image_transformations")
    op.drop_table("catalog_image_transformations")

    op.drop_index("ix_image_asset_status", table_name="catalog_image_assets")
    op.drop_index("ix_image_asset_normalized_hash", table_name="catalog_image_assets")
    op.drop_index("ix_image_asset_original_hash", table_name="catalog_image_assets")
    op.drop_index("ix_image_asset_source_product", table_name="catalog_image_assets")
    op.drop_table("catalog_image_assets")
