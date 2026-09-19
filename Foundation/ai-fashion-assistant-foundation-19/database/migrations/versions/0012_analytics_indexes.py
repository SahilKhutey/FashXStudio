"""analytics query indexes

Revision ID: 0012_analytics_indexes
Revises: 0011_tryon_feedback_instrumentation
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0012_analytics_indexes"
down_revision: str | None = "0011_tryon_feedback_instrumentation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_domain_events_type_occurred_user",
        "domain_events",
        ["event_type", "occurred_at", "user_id"],
        unique=False,
    )
    op.create_index(
        "ix_tryon_feedback_created_at",
        "tryon_feedback",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_wardrobe_items_saved_at",
        "wardrobe_items",
        ["saved_at"],
        unique=False,
    )
    op.create_index(
        "ix_buy_clicks_clicked_at",
        "buy_clicks",
        ["clicked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_buy_clicks_clicked_at", table_name="buy_clicks")
    op.drop_index("ix_wardrobe_items_saved_at", table_name="wardrobe_items")
    op.drop_index("ix_tryon_feedback_created_at", table_name="tryon_feedback")
    op.drop_index("ix_domain_events_type_occurred_user", table_name="domain_events")
