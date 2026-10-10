"""catalog sources, rights flags, provenance columns, category map, and ingest runs

Revision ID: 0018_catalog_sources_and_provenance
Revises: 0017_tryon_provider_tracking
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_catalog_sources_and_provenance"
down_revision: str | None = "0017_tryon_provider_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_DEMO_SOURCE_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    # 1. Create catalog_sources table
    op.create_table(
        "catalog_sources",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),  # api | feed_url | file_drop | manual
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),  # pending | cleared | suspended
        sa.Column("rights_display", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rights_tryon", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("image_policy", sa.Text(), nullable=False, server_default="hotlink"),  # hotlink | mirror
        sa.Column("refresh_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("max_rps", sa.Numeric(5, 2), nullable=False, server_default="2"),
        sa.Column("terms_url", sa.Text(), nullable=True),
        sa.Column("terms_checked_on", sa.Date(), nullable=True),
        sa.Column("takedown_contact", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("status in ('pending','cleared','suspended')", name="ck_source_status"),
        sa.CheckConstraint("kind in ('api','feed_url','file_drop','manual')", name="ck_source_kind"),
        sa.CheckConstraint("image_policy in ('hotlink','mirror')", name="ck_source_image_policy"),
        sa.CheckConstraint("rights_tryon = false OR image_policy = 'mirror'", name="ck_tryon_requires_mirror"),
    )

    # 2. Seed initial demo source for existing test data
    op.execute(
        sa.text(
            f"INSERT INTO catalog_sources (id, slug, name, kind, status, rights_display, rights_tryon, image_policy, refresh_hours, max_rps, notes) "
            f"VALUES ('{SEED_DEMO_SOURCE_ID}', 'seed-demo', 'Seed Demo Catalog', 'manual', 'suspended', false, false, 'hotlink', 24, 2, 'Default suspended source for test/demo fixtures')"
        )
    )

    # 3. Add provenance columns to merchant_products
    op.add_column("merchant_products", sa.Column("source_id", sa.Uuid(), sa.ForeignKey("catalog_sources.id", ondelete="SET NULL"), nullable=True))
    op.add_column("merchant_products", sa.Column("item_group_id", sa.Text(), nullable=True))
    op.add_column("merchant_products", sa.Column("content_hash", sa.Text(), nullable=True))
    op.add_column("merchant_products", sa.Column("status", sa.Text(), nullable=False, server_default="active"))
    op.add_column("merchant_products", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("merchant_products", sa.Column("price_checked_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        sa.text(f"UPDATE merchant_products SET source_id = '{SEED_DEMO_SOURCE_ID}' WHERE source_id IS NULL")
    )

    op.create_check_constraint(
        "ck_product_status", "merchant_products", "status in ('active','stale','removed','blocked')"
    )
    op.create_index(
        "uq_product_source_pid",
        "merchant_products",
        ["source_id", "source_product_id"],
        unique=True,
    )
    op.create_index(
        "ix_product_group",
        "merchant_products",
        ["source_id", "item_group_id"],
    )

    # 4. Create category_map table
    op.create_table(
        "category_map",
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_category", sa.Text(), nullable=False),
        sa.Column("taxonomy_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("source_id", "source_category"),
    )

    # 5. Create ingest_runs table
    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="running"),
        sa.Column("counts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status in ('running','ok','failed','aborted')", name="ck_ingest_run_status"
        ),
    )
    op.create_index("ix_ingest_runs_source", "ingest_runs", ["source_id", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_runs_source", table_name="ingest_runs")
    op.drop_table("ingest_runs")
    op.drop_table("category_map")
    op.drop_index("ix_product_group", table_name="merchant_products")
    op.drop_index("uq_product_source_pid", table_name="merchant_products")
    op.drop_constraint("ck_product_status", "merchant_products", type_="check")
    op.drop_column("merchant_products", "price_checked_at")
    op.drop_column("merchant_products", "last_seen_at")
    op.drop_column("merchant_products", "status")
    op.drop_column("merchant_products", "content_hash")
    op.drop_column("merchant_products", "item_group_id")
    op.drop_column("merchant_products", "source_id")
    op.drop_table("catalog_sources")
