"""Add shopper_profiles, profile_category_sizes, and profile_measurements tables

Revision ID: 0036_add_shopper_profiles
Revises: 0035_add_account_lifecycle_tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036_add_shopper_profiles"
down_revision: str | None = "0035_add_account_lifecycle_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create shopper_profiles table
    op.create_table(
        "shopper_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("preferred_size_system", sa.String(length=8), nullable=True),
        sa.Column("preferred_fit", sa.String(length=24), nullable=True),
        sa.Column("style_preferences", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("preferred_colors", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("product_categories", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("shopping_preferences", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
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
        sa.CheckConstraint(
            "height_cm IS NULL OR (height_cm >= 80 AND height_cm <= 250)",
            name="ck_shopper_profiles_height",
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR (weight_kg >= 20 AND weight_kg <= 400)",
            name="ck_shopper_profiles_weight",
        ),
        sa.CheckConstraint("version >= 1", name="ck_shopper_profiles_version"),
    )
    op.create_index("ix_shopper_profiles_user_id", "shopper_profiles", ["user_id"])
    op.create_index("ix_shopper_profiles_updated_at", "shopper_profiles", ["updated_at"])

    # 2. Create profile_category_sizes table
    op.create_table(
        "profile_category_sizes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category_code", sa.String(length=64), nullable=False),
        sa.Column("size_system", sa.String(length=8), nullable=False),
        sa.Column("size_label", sa.String(length=32), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "category_code", name="uq_profile_category_size"),
    )
    op.create_index("ix_profile_category_sizes_user", "profile_category_sizes", ["user_id"])

    # 3. Create profile_measurements table
    op.create_table(
        "profile_measurements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("measurement_type", sa.String(length=32), nullable=False),
        sa.Column("value_cm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("source", sa.String(length=24), server_default="USER_ENTERED", nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("consent_record_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("value_cm > 0", name="ck_profile_measurements_value"),
    )
    op.create_index(
        "ix_profile_measurements_user_type",
        "profile_measurements",
        ["user_id", "measurement_type"],
    )


def downgrade() -> None:
    # 3. Drop profile_measurements table
    op.drop_index("ix_profile_measurements_user_type", table_name="profile_measurements")
    op.drop_table("profile_measurements")

    # 2. Drop profile_category_sizes table
    op.drop_index("ix_profile_category_sizes_user", table_name="profile_category_sizes")
    op.drop_table("profile_category_sizes")

    # 1. Drop shopper_profiles table
    op.drop_index("ix_shopper_profiles_updated_at", table_name="shopper_profiles")
    op.drop_index("ix_shopper_profiles_user_id", table_name="shopper_profiles")
    op.drop_table("shopper_profiles")
