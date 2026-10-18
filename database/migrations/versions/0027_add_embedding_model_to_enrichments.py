"""Add embedding_model to garment_enrichments

Revision ID: 0027_embedding_model
Revises: 0026_mobile_contract_reconcile
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027_embedding_model"
down_revision: str | None = "0026_mobile_contract_reconcile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("garment_enrichments") as b:
        b.add_column(sa.Column("embedding_model", sa.String(length=128), nullable=True))
        b.create_index("ix_garment_enrichments_embedding_model", ["embedding_model"])


def downgrade() -> None:
    with op.batch_alter_table("garment_enrichments") as b:
        b.drop_index("ix_garment_enrichments_embedding_model")
        b.drop_column("embedding_model")
