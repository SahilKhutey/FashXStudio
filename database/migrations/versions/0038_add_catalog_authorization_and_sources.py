"""Add catalog authorization, source registry, permissions, evidence, and takedowns

Revision ID: 0038_add_catalog_authorization_and_sources
Revises: 0037_add_user_media_and_uploads
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038_add_catalog_authorization_and_sources"
down_revision: str | None = "0037_add_user_media_and_uploads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend merchants table with verification and contact fields
    op.add_column("merchants", sa.Column("legal_name", sa.String(length=255), nullable=True))
    op.add_column("merchants", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("merchants", sa.Column("website", sa.String(length=255), nullable=True))
    op.add_column(
        "merchants",
        sa.Column("country_code", sa.String(length=8), server_default="IN", nullable=False),
    )
    op.add_column(
        "merchants", sa.Column("registration_reference", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "merchants",
        sa.Column(
            "verification_status", sa.String(length=32), server_default="UNVERIFIED", nullable=False
        ),
    )
    op.add_column("merchants", sa.Column("primary_contact_id", sa.Uuid(), nullable=True))
    op.add_column("merchants", sa.Column("technical_contact_id", sa.Uuid(), nullable=True))
    op.add_column("merchants", sa.Column("takedown_contact_id", sa.Uuid(), nullable=True))
    op.add_column(
        "merchants",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.add_column(
        "merchants",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_merchants_verification_status", "merchants", ["verification_status"])
    op.create_index("ix_merchants_legal_name", "merchants", ["legal_name"])

    # 2. Extend catalog_sources table
    op.add_column(
        "catalog_sources",
        sa.Column(
            "merchant_id",
            sa.Uuid(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column("catalog_sources", sa.Column("source_name", sa.String(length=160), nullable=True))
    op.add_column("catalog_sources", sa.Column("source_type", sa.String(length=32), nullable=True))
    op.add_column(
        "catalog_sources", sa.Column("source_owner", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "catalog_sources", sa.Column("provider_name", sa.String(length=100), nullable=True)
    )
    op.add_column("catalog_sources", sa.Column("source_description", sa.Text(), nullable=True))
    op.add_column(
        "catalog_sources", sa.Column("access_method", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "catalog_sources", sa.Column("credential_secret_ref", sa.String(length=512), nullable=True)
    )
    op.add_column(
        "catalog_sources",
        sa.Column(
            "source_status", sa.String(length=32), server_default="PENDING_REVIEW", nullable=False
        ),
    )
    op.add_column(
        "catalog_sources",
        sa.Column("market_codes", sa.JSON(), server_default="[]", nullable=False),
    )
    op.add_column(
        "catalog_sources",
        sa.Column("category_codes", sa.JSON(), server_default="[]", nullable=False),
    )
    op.add_column(
        "catalog_sources", sa.Column("source_terms_version", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "catalog_sources",
        sa.Column("authorization_reference", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "catalog_sources", sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "catalog_sources", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "catalog_sources", sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "catalog_sources",
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "catalog_sources",
        sa.Column("last_authorization_check_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "catalog_sources",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("idx_catalog_sources_merchant", "catalog_sources", ["merchant_id"])
    op.create_index("idx_catalog_sources_status", "catalog_sources", ["source_status"])
    op.create_index("idx_catalog_sources_expiry", "catalog_sources", ["expires_at"])

    # 3. Create catalog_authorization_evidence table
    op.create_table(
        "catalog_authorization_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("document_reference", sa.String(length=512), nullable=False),
        sa.Column("document_sha256", sa.String(length=64), nullable=True),
        sa.Column("agreement_reference", sa.String(length=255), nullable=True),
        sa.Column("agreement_version", sa.String(length=100), nullable=True),
        sa.Column("granted_by_name", sa.String(length=255), nullable=True),
        sa.Column("granted_by_role", sa.String(length=160), nullable=True),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=24),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_catalog_auth_evidence_source", "catalog_authorization_evidence", ["source_id"]
    )
    op.create_index(
        "ix_catalog_auth_evidence_status", "catalog_authorization_evidence", ["verification_status"]
    )

    # 4. Create catalog_source_permissions table
    op.create_table(
        "catalog_source_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("permission_code", sa.String(length=48), nullable=False),
        sa.Column(
            "permission_status",
            sa.String(length=16),
            server_default="GRANTED",
            nullable=False,
        ),
        sa.Column("granted_by", sa.String(length=255), nullable=False),
        sa.Column(
            "evidence_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_authorization_evidence.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scope_categories", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("scope_markets", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("processor_restrictions", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("storage_limit_days", sa.Integer(), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_source_permissions_source", "catalog_source_permissions", ["source_id"])
    op.create_index(
        "idx_source_permissions_code", "catalog_source_permissions", ["permission_code"]
    )
    op.create_index("idx_source_permissions_expiry", "catalog_source_permissions", ["expires_at"])
    op.create_index(
        "idx_source_permissions_lookup",
        "catalog_source_permissions",
        ["source_id", "permission_code", "permission_status"],
    )

    # 5. Create catalog_takedown_requests table
    op.create_table(
        "catalog_takedown_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason_code", sa.String(length=48), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("request_reference", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            sa.String(length=24),
            server_default="RECEIVED",
            nullable=False,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("affected_product_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("affected_asset_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("assigned_reviewer", sa.Uuid(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_catalog_takedown_source", "catalog_takedown_requests", ["source_id"])
    op.create_index("ix_catalog_takedown_status", "catalog_takedown_requests", ["status"])

    # 6. Create catalog_authorization_decisions audit table
    op.create_table(
        "catalog_authorization_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.String(length=255), nullable=True),
        sa.Column("operation", sa.String(length=48), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=True),
        sa.Column("processor_id", sa.String(length=64), nullable=True),
        sa.Column("market", sa.String(length=16), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_catalog_auth_decision_source", "catalog_authorization_decisions", ["source_id"]
    )
    op.create_index(
        "ix_catalog_auth_decision_time", "catalog_authorization_decisions", ["evaluated_at"]
    )
    op.create_index(
        "ix_catalog_auth_decision_decision", "catalog_authorization_decisions", ["decision"]
    )


def downgrade() -> None:
    # 6. Drop catalog_authorization_decisions
    op.drop_index("ix_catalog_auth_decision_decision", table_name="catalog_authorization_decisions")
    op.drop_index("ix_catalog_auth_decision_time", table_name="catalog_authorization_decisions")
    op.drop_index("ix_catalog_auth_decision_source", table_name="catalog_authorization_decisions")
    op.drop_table("catalog_authorization_decisions")

    # 5. Drop catalog_takedown_requests
    op.drop_index("ix_catalog_takedown_status", table_name="catalog_takedown_requests")
    op.drop_index("ix_catalog_takedown_source", table_name="catalog_takedown_requests")
    op.drop_table("catalog_takedown_requests")

    # 4. Drop catalog_source_permissions
    op.drop_index("idx_source_permissions_lookup", table_name="catalog_source_permissions")
    op.drop_index("idx_source_permissions_expiry", table_name="catalog_source_permissions")
    op.drop_index("idx_source_permissions_code", table_name="catalog_source_permissions")
    op.drop_index("idx_source_permissions_source", table_name="catalog_source_permissions")
    op.drop_table("catalog_source_permissions")

    # 3. Drop catalog_authorization_evidence
    op.drop_index("ix_catalog_auth_evidence_status", table_name="catalog_authorization_evidence")
    op.drop_index("ix_catalog_auth_evidence_source", table_name="catalog_authorization_evidence")
    op.drop_table("catalog_authorization_evidence")

    # 2. Drop catalog_sources extension columns
    op.drop_index("idx_catalog_sources_expiry", table_name="catalog_sources")
    op.drop_index("idx_catalog_sources_status", table_name="catalog_sources")
    op.drop_index("idx_catalog_sources_merchant", table_name="catalog_sources")
    op.drop_column("catalog_sources", "updated_at")
    op.drop_column("catalog_sources", "last_authorization_check_at")
    op.drop_column("catalog_sources", "last_successful_sync_at")
    op.drop_column("catalog_sources", "next_review_at")
    op.drop_column("catalog_sources", "expires_at")
    op.drop_column("catalog_sources", "effective_at")
    op.drop_column("catalog_sources", "authorization_reference")
    op.drop_column("catalog_sources", "source_terms_version")
    op.drop_column("catalog_sources", "category_codes")
    op.drop_column("catalog_sources", "market_codes")
    op.drop_column("catalog_sources", "source_status")
    op.drop_column("catalog_sources", "credential_secret_ref")
    op.drop_column("catalog_sources", "access_method")
    op.drop_column("catalog_sources", "source_description")
    op.drop_column("catalog_sources", "provider_name")
    op.drop_column("catalog_sources", "source_owner")
    op.drop_column("catalog_sources", "source_type")
    op.drop_column("catalog_sources", "source_name")
    op.drop_column("catalog_sources", "merchant_id")

    # 1. Drop merchants extension columns
    op.drop_index("ix_merchants_legal_name", table_name="merchants")
    op.drop_index("ix_merchants_verification_status", table_name="merchants")
    op.drop_column("merchants", "updated_at")
    op.drop_column("merchants", "created_at")
    op.drop_column("merchants", "takedown_contact_id")
    op.drop_column("merchants", "technical_contact_id")
    op.drop_column("merchants", "primary_contact_id")
    op.drop_column("merchants", "verification_status")
    op.drop_column("merchants", "registration_reference")
    op.drop_column("merchants", "country_code")
    op.drop_column("merchants", "website")
    op.drop_column("merchants", "display_name")
    op.drop_column("merchants", "legal_name")
