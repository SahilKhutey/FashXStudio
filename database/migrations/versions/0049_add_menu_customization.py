"""Add menu customization, revisions, theme/layout/component definitions and migrations

Revision ID: 0049_add_menu_customization
Revises: 0048_add_catalog_search
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0049_add_menu_customization"
down_revision: str | None = "0048_add_catalog_search"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. theme_definitions
    op.create_table(
        "theme_definitions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preview_image_url", sa.Text(), nullable=True),
        sa.Column("tokens", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("supported_layouts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("supported_components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("accessibility", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "version", name="pk_theme_definitions"),
        sa.UniqueConstraint("id", "version", name="uq_theme_definitions_id_version"),
    )
    op.create_index("ix_theme_definitions_status", "theme_definitions", ["status"])

    # 2. layout_definitions
    op.create_table(
        "layout_definitions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("supported_slots", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allowed_components_by_slot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("default_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("responsive_profiles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "version", name="pk_layout_definitions"),
        sa.UniqueConstraint("id", "version", name="uq_layout_definitions_id_version"),
    )
    op.create_index("ix_layout_definitions_status", "layout_definitions", ["status"])

    # 3. component_definitions
    op.create_table(
        "component_definitions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("allowed_slots", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("property_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("default_props", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("accessibility", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("renderer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "version", name="pk_component_definitions"),
        sa.UniqueConstraint("id", "version", name="uq_component_definitions_id_version"),
    )
    op.create_index("ix_component_definitions_status", "component_definitions", ["status"])

    # 4. menu_customizations
    op.create_table(
        "menu_customizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("menu_id", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_menu_customizations"),
        sa.UniqueConstraint("organization_id", "menu_id", name="uq_customization_org_menu"),
    )
    op.create_index("ix_menu_customizations_org_menu", "menu_customizations", ["organization_id", "menu_id"])
    op.create_index("ix_menu_customizations_organization_id", "menu_customizations", ["organization_id"])
    op.create_index("ix_menu_customizations_menu_id", "menu_customizations", ["menu_id"])

    # 5. customization_revisions
    op.create_table(
        "customization_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customization_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("menu_id", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customization_id"],
            ["menu_customizations.id"],
            name="fk_customization_revisions_customization_id_menu_customizations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customization_revisions"),
        sa.UniqueConstraint("customization_id", "revision", name="uq_revision_customization_rev"),
    )
    op.create_index("ix_customization_revisions_org_menu", "customization_revisions", ["organization_id", "menu_id"])
    op.create_index("ix_customization_revisions_customization_id", "customization_revisions", ["customization_id"])

    # 6. configuration_migrations
    op.create_table(
        "configuration_migrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_version", sa.Text(), nullable=False),
        sa.Column("target_version", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_configuration_migrations"),
        sa.UniqueConstraint("source_version", "target_version", name="uq_migration_source_target"),
    )


def downgrade() -> None:
    op.drop_table("configuration_migrations")
    op.drop_table("customization_revisions")
    op.drop_table("menu_customizations")
    op.drop_table("component_definitions")
    op.drop_table("layout_definitions")
    op.drop_table("theme_definitions")
