"""Add Phase 08.5 feedback loop tables (events, ledger, outbox, projections, consents)

Revision ID: 0060_add_feedback_loop_tables
Revises: 0059_add_personalized_ranking_tables
Create Date: 2026-11-27 09:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0060_add_feedback_loop_tables"
down_revision: str | None = "0059_add_personalized_ranking_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feedback_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("feedback_class", sa.String(length=30), nullable=False),
        sa.Column("subject_type", sa.String(length=40), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="mobile"),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("context_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("consent_revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "processing_status", sa.String(length=30), nullable=False, server_default="PENDING"
        ),
        sa.UniqueConstraint("event_id", name="uq_feedback_events_event_id"),
    )
    op.create_index(
        "ix_feedback_events_user_occurred", "feedback_events", ["user_id", "occurred_at"]
    )
    op.create_index(
        "ix_feedback_events_subject_occurred",
        "feedback_events",
        ["subject_type", "subject_id", "occurred_at"],
    )

    op.create_table(
        "feedback_processing",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_feedback_processing_user_id", "feedback_processing", ["user_id"])

    op.create_table(
        "feedback_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=64), nullable=False, server_default="feedback.events"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("event_id", name="uq_feedback_outbox_event_id"),
    )
    op.create_index(
        "ix_feedback_outbox_status_created", "feedback_outbox", ["status", "created_at"]
    )

    op.create_table(
        "shopper_product_reactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("reaction", sa.String(length=20), nullable=False, server_default="NONE"),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_shopper_product_reactions_user_product",
        ),
        sa.CheckConstraint(
            "reaction IN ('LIKE', 'DISLIKE', 'NONE')",
            name="ck_shopper_product_reaction_state",
        ),
    )
    op.create_index("ix_shopper_product_reactions_user", "shopper_product_reactions", ["user_id"])

    op.create_table(
        "shopper_saved_products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("merchant_offer_id", sa.String(length=128), nullable=True),
        sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "saved_at",
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
        sa.UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_shopper_saved_products_user_product",
        ),
    )
    op.create_index(
        "ix_shopper_saved_products_user_saved",
        "shopper_saved_products",
        ["user_id", "is_saved"],
    )

    op.create_table(
        "shopper_consent_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False, server_default="2026.1"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="app"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_shopper_consent_user_purpose",
        "shopper_consent_records",
        ["user_id", "purpose", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_shopper_consent_user_purpose", table_name="shopper_consent_records")
    op.drop_table("shopper_consent_records")

    op.drop_index("ix_shopper_saved_products_user_saved", table_name="shopper_saved_products")
    op.drop_table("shopper_saved_products")

    op.drop_index("ix_shopper_product_reactions_user", table_name="shopper_product_reactions")
    op.drop_table("shopper_product_reactions")

    op.drop_index("ix_feedback_outbox_status_created", table_name="feedback_outbox")
    op.drop_table("feedback_outbox")

    op.drop_index("ix_feedback_processing_user_id", table_name="feedback_processing")
    op.drop_table("feedback_processing")

    op.drop_index("ix_feedback_events_subject_occurred", table_name="feedback_events")
    op.drop_index("ix_feedback_events_user_occurred", table_name="feedback_events")
    op.drop_table("feedback_events")
