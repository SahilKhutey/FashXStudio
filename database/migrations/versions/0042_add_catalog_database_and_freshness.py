"""Add catalog database freshness, price history, variants, offer sizes, provenance, and performance indexes

Revision ID: 0042_add_catalog_database_and_freshness
Revises: 0041_add_catalog_image_pipeline
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0042_add_catalog_database_and_freshness"
down_revision: str | None = "0041_add_catalog_image_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend merchants table
    op.add_column(
        "merchants",
        sa.Column("operational_status", sa.String(length=32), server_default="ACTIVE", nullable=False),
    )

    # 2. Extend catalog_sources table
    op.add_column("catalog_sources", sa.Column("adapter_name", sa.String(length=64), nullable=True))
    op.add_column("catalog_sources", sa.Column("adapter_version", sa.String(length=32), nullable=True))
    op.add_column(
        "catalog_sources", sa.Column("last_failed_sync_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("catalog_sources", sa.Column("permission_revision", sa.Integer(), nullable=True))
    op.add_column(
        "catalog_sources",
        sa.Column("freshness_policy_hours", sa.Integer(), server_default="24", nullable=True),
    )
    op.create_index(
        "ix_catalog_sources_merchant_status",
        "catalog_sources",
        ["merchant_id", "source_status"],
    )

    # 3. Extend canonical_garments table
    op.add_column("canonical_garments", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("canonical_garments", sa.Column("material", sa.String(length=255), nullable=True))
    op.add_column("canonical_garments", sa.Column("color_family", sa.String(length=64), nullable=True))
    op.add_column(
        "canonical_garments",
        sa.Column("identity_status", sa.String(length=32), server_default="VERIFIED", nullable=False),
    )
    op.create_index(
        "ix_garments_category_brand",
        "canonical_garments",
        ["category", "brand_id"],
    )
    op.create_index(
        "ix_garments_brand",
        "canonical_garments",
        ["brand_id"],
    )

    # 4. Extend merchant_products table
    op.add_column("merchant_products", sa.Column("source_variant_id", sa.String(length=255), nullable=True))
    op.add_column("merchant_products", sa.Column("source_category", sa.String(length=255), nullable=True))
    op.add_column("merchant_products", sa.Column("currency", sa.String(length=3), nullable=True))
    op.add_column("merchant_products", sa.Column("price_minor", sa.BigInteger(), nullable=True))
    op.add_column(
        "merchant_products",
        sa.Column("availability", sa.String(length=32), server_default="IN_STOCK", nullable=True),
    )
    op.add_column(
        "merchant_products", sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_products",
        sa.Column(
            "ingest_run_id",
            sa.Uuid(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_products",
        sa.Column(
            "first_ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_products", sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_products", sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_products", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_products", sa.Column("source_schema_version", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "merchant_products",
        sa.Column("sync_status", sa.String(length=32), server_default="CURRENT", nullable=False),
    )
    op.add_column(
        "merchant_products",
        sa.Column("takedown_status", sa.String(length=32), server_default="NONE", nullable=False),
    )
    op.add_column("merchant_products", sa.Column("takedown_id", sa.Uuid(), nullable=True))
    op.create_index(
        "ix_merchant_products_merchant_status",
        "merchant_products",
        ["merchant_id", "status"],
    )

    # 5. Extend merchant_offers table
    op.add_column(
        "merchant_offers",
        sa.Column(
            "merchant_product_id",
            sa.Uuid(),
            sa.ForeignKey("merchant_products.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "ingest_run_id",
            sa.Uuid(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
    )
    op.add_column(
        "merchant_offers",
        sa.Column("availability", sa.String(length=32), server_default="IN_STOCK", nullable=False),
    )
    op.add_column("merchant_offers", sa.Column("original_price_minor", sa.BigInteger(), nullable=True))
    op.add_column(
        "merchant_offers", sa.Column("discount_percentage", sa.Numeric(precision=5, scale=2), nullable=True)
    )
    op.add_column(
        "merchant_offers", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_offers", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_offers", sa.Column("last_price_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_offers",
        sa.Column("last_availability_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "merchant_offers", sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "first_ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "last_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column("sync_status", sa.String(length=32), server_default="CURRENT", nullable=False),
    )
    op.add_column(
        "merchant_offers",
        sa.Column("takedown_status", sa.String(length=32), server_default="NONE", nullable=False),
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.add_column(
        "merchant_offers",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_merchant_offers_merchant_status",
        "merchant_offers",
        ["merchant_id", "status"],
    )
    op.create_index(
        "ix_merchant_offers_price_currency",
        "merchant_offers",
        ["currency", "price_minor"],
    )
    op.create_index(
        "ix_merchant_offers_availability",
        "merchant_offers",
        ["availability"],
    )
    op.create_index(
        "ix_merchant_offers_merchant_product",
        "merchant_offers",
        ["merchant_product_id"],
    )

    # 6. Create size_definitions table
    op.create_table(
        "size_definitions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("size_system", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("standardized_label", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "size_system", "category", "standardized_label", name="uq_size_definition"
        ),
    )
    op.create_index(
        "ix_size_definitions_system_cat",
        "size_definitions",
        ["size_system", "category"],
    )

    # 7. Create product_variants table
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "canonical_garment_id",
            sa.Uuid(),
            sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("color_hex", sa.String(length=7), nullable=True),
        sa.Column("size_label", sa.String(length=64), nullable=True),
        sa.Column(
            "size_definition_id",
            sa.Uuid(),
            sa.ForeignKey("size_definitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
    )
    op.create_index(
        "ix_product_variants_garment",
        "product_variants",
        ["canonical_garment_id"],
    )
    op.create_index(
        "ix_product_variants_sku",
        "product_variants",
        ["sku"],
    )

    # 8. Create merchant_offer_sizes table
    op.create_table(
        "merchant_offer_sizes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "merchant_offer_id",
            sa.Uuid(),
            sa.ForeignKey("merchant_offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.Uuid(),
            sa.ForeignKey("product_variants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "size_definition_id",
            sa.Uuid(),
            sa.ForeignKey("size_definitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("raw_size", sa.String(length=64), nullable=False),
        sa.Column("size_system", sa.String(length=16), nullable=True),
        sa.Column("availability", sa.String(length=32), server_default="IN_STOCK", nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("merchant_offer_id", "raw_size", name="uq_offer_raw_size"),
    )
    op.create_index(
        "ix_offer_sizes_size_availability",
        "merchant_offer_sizes",
        ["size_definition_id", "availability"],
    )
    op.create_index(
        "ix_offer_sizes_offer",
        "merchant_offer_sizes",
        ["merchant_offer_id"],
    )

    # 9. Create merchant_offer_price_history table
    op.create_table(
        "merchant_offer_price_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "merchant_offer_id",
            sa.Uuid(),
            sa.ForeignKey("merchant_offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingest_run_id",
            sa.Uuid(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("original_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("change_type", sa.String(length=32), server_default="INITIAL", nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_price_history_offer_observed",
        "merchant_offer_price_history",
        ["merchant_offer_id", "observed_at"],
    )
    op.create_index(
        "ix_price_history_merchant_source",
        "merchant_offer_price_history",
        ["merchant_id", "source_id"],
    )
    op.create_index(
        "ix_price_history_recorded",
        "merchant_offer_price_history",
        ["recorded_at"],
    )

    # 10. Create catalog_provenance_records table
    op.create_table(
        "catalog_provenance_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_name", sa.String(length=64), nullable=False),
        sa.Column("attribute_value", sa.Text(), nullable=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ingest_run_id",
            sa.Uuid(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), server_default="1.000", nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_provenance_entity_attr",
        "catalog_provenance_records",
        ["entity_type", "entity_id", "attribute_name"],
    )
    op.create_index(
        "ix_provenance_source",
        "catalog_provenance_records",
        ["source_id"],
    )
    op.create_index(
        "ix_provenance_run",
        "catalog_provenance_records",
        ["ingest_run_id"],
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("catalog_provenance_records")
    op.drop_table("merchant_offer_price_history")
    op.drop_table("merchant_offer_sizes")
    op.drop_table("product_variants")
    op.drop_table("size_definitions")

    # Drop indexes and columns from merchant_offers
    op.drop_index("ix_merchant_offers_merchant_product", table_name="merchant_offers")
    op.drop_index("ix_merchant_offers_availability", table_name="merchant_offers")
    op.drop_index("ix_merchant_offers_price_currency", table_name="merchant_offers")
    op.drop_index("ix_merchant_offers_merchant_status", table_name="merchant_offers")
    op.drop_column("merchant_offers", "updated_at")
    op.drop_column("merchant_offers", "created_at")
    op.drop_column("merchant_offers", "takedown_status")
    op.drop_column("merchant_offers", "sync_status")
    op.drop_column("merchant_offers", "last_changed_at")
    op.drop_column("merchant_offers", "first_ingested_at")
    op.drop_column("merchant_offers", "source_updated_at")
    op.drop_column("merchant_offers", "last_availability_verified_at")
    op.drop_column("merchant_offers", "last_price_verified_at")
    op.drop_column("merchant_offers", "last_verified_at")
    op.drop_column("merchant_offers", "last_seen_at")
    op.drop_column("merchant_offers", "discount_percentage")
    op.drop_column("merchant_offers", "original_price_minor")
    op.drop_column("merchant_offers", "availability")
    op.drop_column("merchant_offers", "status")
    op.drop_column("merchant_offers", "ingest_run_id")
    op.drop_column("merchant_offers", "source_id")
    op.drop_column("merchant_offers", "merchant_product_id")

    # Drop indexes and columns from merchant_products
    op.drop_index("ix_merchant_products_merchant_status", table_name="merchant_products")
    op.drop_column("merchant_products", "takedown_id")
    op.drop_column("merchant_products", "takedown_status")
    op.drop_column("merchant_products", "sync_status")
    op.drop_column("merchant_products", "source_schema_version")
    op.drop_column("merchant_products", "last_verified_at")
    op.drop_column("merchant_products", "last_changed_at")
    op.drop_column("merchant_products", "last_ingested_at")
    op.drop_column("merchant_products", "first_ingested_at")
    op.drop_column("merchant_products", "ingest_run_id")
    op.drop_column("merchant_products", "source_updated_at")
    op.drop_column("merchant_products", "availability")
    op.drop_column("merchant_products", "price_minor")
    op.drop_column("merchant_products", "currency")
    op.drop_column("merchant_products", "source_category")
    op.drop_column("merchant_products", "source_variant_id")

    # Drop indexes and columns from canonical_garments
    op.drop_index("ix_garments_brand", table_name="canonical_garments")
    op.drop_index("ix_garments_category_brand", table_name="canonical_garments")
    op.drop_column("canonical_garments", "identity_status")
    op.drop_column("canonical_garments", "color_family")
    op.drop_column("canonical_garments", "material")
    op.drop_column("canonical_garments", "description")

    # Drop indexes and columns from catalog_sources
    op.drop_index("ix_catalog_sources_merchant_status", table_name="catalog_sources")
    op.drop_column("catalog_sources", "freshness_policy_hours")
    op.drop_column("catalog_sources", "permission_revision")
    op.drop_column("catalog_sources", "last_failed_sync_at")
    op.drop_column("catalog_sources", "adapter_version")
    op.drop_column("catalog_sources", "adapter_name")

    # Drop column from merchants
    op.drop_column("merchants", "operational_status")
