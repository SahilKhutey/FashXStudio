"""B2B multi-tenant tables: tenants, domains, keys, products, members, widget sessions, usage

Revision ID: 0025_b2b_multi_tenant
Revises: 0024_experiment_exposures
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0025_b2b_multi_tenant"
down_revision: str | None = "0024_experiment_exposures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. tenants
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False, server_default="pilot"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # 2. tenant_domains
    op.create_table(
        "tenant_domains",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("domain", name="uq_tenant_domains_domain"),
    )
    op.create_index("ix_tenant_domains_tenant_id", "tenant_domains", ["tenant_id"])
    op.create_index("ix_tenant_domains_domain", "tenant_domains", ["domain"])

    # 3. tenant_keys
    op.create_table(
        "tenant_keys",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key_prefix", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, server_default="default"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("key_hash", name="uq_tenant_keys_key_hash"),
    )
    op.create_index("ix_tenant_keys_tenant_id", "tenant_keys", ["tenant_id"])
    op.create_index("ix_tenant_keys_key_hash", "tenant_keys", ["key_hash"])

    # 4. tenant_products
    op.create_table(
        "tenant_products",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_product_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("handle", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("size_chart", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("tenant_id", "external_product_id", name="uq_tenant_external_product"),
    )
    op.create_index("ix_tenant_products_tenant_id", "tenant_products", ["tenant_id"])
    op.create_index("ix_tenant_products_external_product_id", "tenant_products", ["external_product_id"])

    # 5. tenant_members
    op.create_table(
        "tenant_members",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_member"),
    )
    op.create_index("ix_tenant_members_tenant_id", "tenant_members", ["tenant_id"])
    op.create_index("ix_tenant_members_user_id", "tenant_members", ["user_id"])

    # 6. widget_sessions
    op.create_table(
        "widget_sessions",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_token", sa.Text(), nullable=False),
        sa.Column("shopper_ip_hash", sa.Text(), nullable=False),
        sa.Column("external_product_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("session_token", name="uq_widget_sessions_token"),
    )
    op.create_index("ix_widget_sessions_tenant_id", "widget_sessions", ["tenant_id"])
    op.create_index("ix_widget_sessions_session_token", "widget_sessions", ["session_token"])

    # 7. tenant_usage
    op.create_table(
        "tenant_usage",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("billing_period", sa.Text(), nullable=False),
        sa.Column("tryon_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_inr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("tenant_id", "billing_period", name="uq_tenant_billing_period"),
    )
    op.create_index("ix_tenant_usage_tenant_id", "tenant_usage", ["tenant_id"])
    op.create_index("ix_tenant_usage_billing_period", "tenant_usage", ["billing_period"])


def downgrade() -> None:
    op.drop_table("tenant_usage")
    op.drop_table("widget_sessions")
    op.drop_table("tenant_members")
    op.drop_table("tenant_products")
    op.drop_table("tenant_keys")
    op.drop_table("tenant_domains")
    op.drop_table("tenants")
