"""add catalog runtime identity and searchable garment fields"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008_catalog_runtime"
down_revision: str | Sequence[str] | None = "0007_profile_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "merchant_products",
        sa.Column(
            "canonical_garment_id",
            sa.UUID(),
            sa.ForeignKey("canonical_garments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_merchant_products_canonical_garment_id",
        "merchant_products",
        ["canonical_garment_id"],
    )

    op.add_column("canonical_garments", sa.Column("display_name", sa.Text(), nullable=True))
    op.execute(
        "UPDATE canonical_garments SET display_name = COALESCE(NULLIF(subcategory, ''), category)"
    )
    op.alter_column("canonical_garments", "display_name", nullable=False)

    op.create_unique_constraint(
        "uq_merchant_offer_source",
        "merchant_offers",
        ["merchant_id", "source_product_id"],
    )
    op.create_index(
        "ix_canonical_garments_display_name",
        "canonical_garments",
        ["display_name"],
    )
    op.create_index(
        "ix_merchant_offers_stock_price",
        "merchant_offers",
        ["in_stock", "price_minor", "garment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_merchant_offers_stock_price", table_name="merchant_offers")
    op.drop_index("ix_canonical_garments_display_name", table_name="canonical_garments")
    op.drop_constraint("uq_merchant_offer_source", "merchant_offers", type_="unique")
    op.drop_column("canonical_garments", "display_name")
    op.drop_index("ix_merchant_products_canonical_garment_id", table_name="merchant_products")
    op.drop_column("merchant_products", "canonical_garment_id")
