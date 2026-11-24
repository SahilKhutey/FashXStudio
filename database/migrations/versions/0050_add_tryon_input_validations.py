"""Add tryon input validations and authorization snapshots (Phase 07.3)

Revision ID: 0050_add_tryon_input_validations
Revises: 0049_add_menu_customization
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0050_add_tryon_input_validations"
down_revision: str | None = "0049_add_menu_customization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. tryon_input_validations
    op.create_table(
        "tryon_input_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tryon_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_version", sa.String(length=64), nullable=False),
        sa.Column("original_sha256", sa.String(length=64), nullable=True),
        sa.Column("normalized_sha256", sa.String(length=64), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "technical_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "visual_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "issues",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tryon_job_id",
            "role",
            "asset_id",
            "asset_version",
            "policy_version",
            name="uq_tryon_input_validations_idempotency",
        ),
    )
    op.create_index("ix_tryon_input_job", "tryon_input_validations", ["tryon_job_id"])
    op.create_index(
        "ix_tryon_input_asset",
        "tryon_input_validations",
        ["asset_id", "asset_version"],
    )
    op.create_index(
        "ix_tryon_input_status",
        "tryon_input_validations",
        ["status", "validated_at"],
    )

    # 2. tryon_input_authorization_snapshots
    op.create_table(
        "tryon_input_authorization_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tryon_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("authorization_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_scope", sa.String(length=64), nullable=False),
        sa.Column("evidence_revision", sa.String(length=64), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=32), nullable=False),
    )
    op.create_index(
        "ix_tryon_auth_snapshot_job",
        "tryon_input_authorization_snapshots",
        ["tryon_job_id"],
    )
    op.create_index(
        "ix_tryon_auth_snapshot_subject",
        "tryon_input_authorization_snapshots",
        ["subject_id", "authorization_type"],
    )


def downgrade() -> None:
    op.drop_table("tryon_input_authorization_snapshots")
    op.drop_table("tryon_input_validations")
