"""Add fashion taxonomy and product classification tables

Revision ID: 0045_add_fashion_taxonomy
Revises: 0044_add_catalog_evaluation_runs
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0045_add_fashion_taxonomy"
down_revision: str | None = "0044_add_catalog_evaluation_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create taxonomy_versions
    op.create_table(
        "taxonomy_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
        sa.Column("locale", sa.String(length=16), server_default="en-IN", nullable=False),
        sa.Column("market", sa.String(length=16), server_default="IN", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_taxonomy_versions_version"),
    )

    # 2. Create taxonomy_categories
    op.create_table(
        "taxonomy_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("taxonomy_version_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=64), nullable=False),
        sa.Column("parent_code", sa.String(length=64), nullable=True),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_leaf", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["taxonomy_version_id"], ["taxonomy_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "taxonomy_version_id", "category_code", name="uq_taxonomy_category_version_code"
        ),
    )
    op.create_index(
        "ix_taxonomy_categories_path",
        "taxonomy_categories",
        ["path"],
        unique=False,
    )
    op.create_index(
        "ix_taxonomy_categories_version",
        "taxonomy_categories",
        ["taxonomy_version_id"],
        unique=False,
    )

    # 3. Create taxonomy_attributes
    op.create_table(
        "taxonomy_attributes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("taxonomy_version_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("attribute_type", sa.String(length=32), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_multi_valued", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("allowed_categories", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("validation_rules", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["taxonomy_version_id"], ["taxonomy_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "taxonomy_version_id",
            "attribute_code",
            name="uq_taxonomy_attribute_version_code",
        ),
    )
    op.create_index(
        "ix_taxonomy_attributes_version",
        "taxonomy_attributes",
        ["taxonomy_version_id"],
        unique=False,
    )

    # 4. Create taxonomy_attribute_values
    op.create_table(
        "taxonomy_attribute_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("value_code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("parent_value_code", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attribute_id"], ["taxonomy_attributes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attribute_id", "value_code", name="uq_taxonomy_attr_value_code"),
    )
    op.create_index(
        "ix_taxonomy_attr_values_attr",
        "taxonomy_attribute_values",
        ["attribute_id"],
        unique=False,
    )

    # 5. Create taxonomy_aliases
    op.create_table(
        "taxonomy_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("taxonomy_version_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_code", sa.String(length=64), nullable=False),
        sa.Column("alias_term", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), server_default="merchant", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["taxonomy_version_id"], ["taxonomy_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_taxonomy_aliases_lookup",
        "taxonomy_aliases",
        ["taxonomy_version_id", "target_type", "alias_term"],
        unique=False,
    )

    # 6. Create product_classifications
    op.create_table(
        "product_classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("garment_id", sa.Uuid(), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.String(length=64), nullable=False),
        sa.Column("garment_type_id", sa.String(length=64), nullable=True),
        sa.Column("style_family", sa.String(length=64), nullable=True),
        sa.Column("intended_audience", sa.String(length=32), nullable=True),
        sa.Column("occasions", sa.JSON(), server_default="[]", nullable=False),
        sa.Column(
            "classification_status",
            sa.String(length=32),
            server_default="VERIFIED",
            nullable=False,
        ),
        sa.Column(
            "classification_source",
            sa.String(length=32),
            server_default="MERCHANT",
            nullable=False,
        ),
        sa.Column("classification_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column(
            "classified_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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
            ["garment_id"], ["canonical_garments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "garment_id",
            "taxonomy_version",
            name="uq_product_classifications_garment_version",
        ),
    )
    op.create_index(
        "ix_product_classifications_cat",
        "product_classifications",
        ["category_id", "garment_type_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_classifications_garment",
        "product_classifications",
        ["garment_id"],
        unique=False,
    )

    # 7. Create product_attribute_values
    op.create_table(
        "product_attribute_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("classification_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_code", sa.String(length=64), nullable=False),
        sa.Column("value_status", sa.String(length=32), server_default="KNOWN", nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["classification_id"], ["product_classifications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classification_id",
            "attribute_code",
            name="uq_product_attr_classification_code",
        ),
    )
    op.create_index(
        "ix_product_attr_values_lookup",
        "product_attribute_values",
        ["attribute_code", "value_status"],
        unique=False,
    )
    op.create_index(
        "ix_product_attr_values_classification",
        "product_attribute_values",
        ["classification_id"],
        unique=False,
    )

    # 8. Create product_attribute_provenance
    op.create_table(
        "product_attribute_provenance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_attribute_value_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=32),
            server_default="UNREVIEWED",
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["product_attribute_value_id"], ["product_attribute_values.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_attr_provenance_val",
        "product_attribute_provenance",
        ["product_attribute_value_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("product_attribute_provenance")
    op.drop_table("product_attribute_values")
    op.drop_table("product_classifications")
    op.drop_table("taxonomy_aliases")
    op.drop_table("taxonomy_attribute_values")
    op.drop_table("taxonomy_attributes")
    op.drop_table("taxonomy_categories")
    op.drop_table("taxonomy_versions")
