"""Add shopper fit profile extensions, measurement history, category fit preferences, and audit events (Phase 08.2)

Revision ID: 0057_add_shopper_fit_profile_and_history
Revises: 0056_add_product_size_data_and_revisions
Create Date: 2026-11-26 09:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0057_add_shopper_fit_profile_and_history"
down_revision: str | None = "0056_add_product_size_data_and_revisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend shopper_profiles
    with op.batch_alter_table("shopper_profiles") as b:
        b.add_column(
            sa.Column(
                "preferred_measurement_unit",
                sa.String(length=8),
                nullable=False,
                server_default="CM",
            )
        )

    # 2. Extend profile_measurements
    with op.batch_alter_table("profile_measurements") as b:
        b.add_column(
            sa.Column(
                "measurement_subject",
                sa.String(length=16),
                nullable=False,
                server_default="BODY",
            )
        )
        b.add_column(sa.Column("original_value", sa.Numeric(precision=8, scale=2), nullable=True))
        b.add_column(
            sa.Column(
                "original_unit",
                sa.String(length=8),
                nullable=False,
                server_default="CM",
            )
        )
        b.add_column(sa.Column("normalized_value", sa.Numeric(precision=8, scale=2), nullable=True))
        b.add_column(
            sa.Column(
                "normalized_unit",
                sa.String(length=8),
                nullable=False,
                server_default="CM",
            )
        )
        b.add_column(
            sa.Column(
                "measurement_method",
                sa.String(length=32),
                nullable=False,
                server_default="SELF_MEASURED",
            )
        )
        b.add_column(
            sa.Column(
                "status",
                sa.String(length=24),
                nullable=False,
                server_default="PROVIDED",
            )
        )
        b.add_column(
            sa.Column(
                "validation_status",
                sa.String(length=24),
                nullable=False,
                server_default="ACCEPTED",
            )
        )
        b.add_column(
            sa.Column(
                "policy_version",
                sa.String(length=20),
                nullable=False,
                server_default="1.0",
            )
        )
        b.add_column(
            sa.Column(
                "schema_version",
                sa.String(length=20),
                nullable=False,
                server_default="1.0",
            )
        )
        b.add_column(sa.Column("measured_at", sa.DateTime(timezone=True), nullable=True))
        b.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        b.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        b.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        b.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        b.add_column(
            sa.Column("version", sa.Integer(), nullable=False, server_default="1")
        )
        b.create_check_constraint("ck_profile_measurements_version", "version >= 1")
        b.create_unique_constraint(
            "uq_profile_measurements_user_type", ["user_id", "measurement_type"]
        )

    # 3. profile_measurement_history table
    op.create_table(
        "profile_measurement_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("measurement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_code", sa.String(length=32), nullable=False),
        sa.Column("previous_value", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("previous_unit", sa.String(length=8), nullable=True),
        sa.Column("new_value", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("new_unit", sa.String(length=8), nullable=True),
        sa.Column("normalized_value", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("change_source", sa.String(length=32), nullable=False, server_default="SHOPPER_UPDATE"),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_profile_meas_history_user_field",
        "profile_measurement_history",
        ["user_id", "field_code"],
    )
    op.create_index(
        "ix_profile_meas_history_changed",
        "profile_measurement_history",
        ["changed_at"],
    )

    # 4. category_fit_preferences table
    op.create_table(
        "category_fit_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("fit_preference", sa.String(length=24), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "category", name="uq_category_fit_preferences_user_cat"),
    )
    op.create_index("ix_category_fit_preferences_user", "category_fit_preferences", ["user_id"])

    # 5. profile_audit_events table
    op.create_table(
        "profile_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_profile_audit_events_user", "profile_audit_events", ["user_id"])
    op.create_index("ix_profile_audit_events_created", "profile_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("profile_audit_events")
    op.drop_table("category_fit_preferences")
    op.drop_table("profile_measurement_history")

    with op.batch_alter_table("profile_measurements") as b:
        b.drop_constraint("uq_profile_measurements_user_type", type_="unique")
        b.drop_constraint("ck_profile_measurements_version", type_="check")
        b.drop_column("version")
        b.drop_column("expires_at")
        b.drop_column("verified_at")
        b.drop_column("updated_at")
        b.drop_column("created_at")
        b.drop_column("measured_at")
        b.drop_column("schema_version")
        b.drop_column("policy_version")
        b.drop_column("validation_status")
        b.drop_column("status")
        b.drop_column("measurement_method")
        b.drop_column("normalized_unit")
        b.drop_column("normalized_value")
        b.drop_column("original_unit")
        b.drop_column("original_value")
        b.drop_column("measurement_subject")

    with op.batch_alter_table("shopper_profiles") as b:
        b.drop_column("preferred_measurement_unit")
