"""Add account lifecycle tables and extend users table

Revision ID: 0035_add_account_lifecycle_tables
Revises: 0034_add_revoked_auth_sessions
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035_add_account_lifecycle_tables"
down_revision: str | None = "0034_add_revoked_auth_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend users table with lifecycle fields
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="ACTIVE",
            nullable=False,
        ),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.add_column(
        "users",
        sa.Column(
            "email_normalized",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_email_normalized",
        "users",
        ["email_normalized"],
        unique=True,
    )

    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "disabled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "deletion_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # 2. Create identity_accounts table
    op.create_table(
        "identity_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column(
            "identity_status",
            sa.String(length=32),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_authenticated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_identity_accounts_provider_subject",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_identity_accounts_user_provider",
        ),
    )
    op.create_index(
        "ix_identity_accounts_user_id",
        "identity_accounts",
        ["user_id"],
    )

    # 3. Create auth_sessions table
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_origin_jti", sa.String(length=255), nullable=True),
        sa.Column("provider_jti", sa.String(length=255), nullable=False),
        sa.Column("device_label", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "session_status",
            sa.String(length=32),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_jti",
            name="uq_auth_sessions_provider_jti",
        ),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_provider_jti", "auth_sessions", ["provider_jti"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_index(
        "ix_auth_sessions_user_status",
        "auth_sessions",
        ["user_id", "session_status"],
    )

    # 4. Create account_deletion_jobs table
    op.create_table(
        "account_deletion_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            server_default="5",
            nullable=False,
        ),
        sa.Column(
            "last_error_code",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "last_error_message",
            sa.Text(),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_account_deletion_jobs_user_id",
        "account_deletion_jobs",
        ["user_id"],
    )
    op.create_index(
        "ix_account_deletion_jobs_status",
        "account_deletion_jobs",
        ["status"],
    )
    op.create_index(
        "ix_account_deletion_jobs_user_status",
        "account_deletion_jobs",
        ["user_id", "status"],
    )


def downgrade() -> None:
    # 4. Drop account_deletion_jobs table
    op.drop_index(
        "ix_account_deletion_jobs_user_status",
        table_name="account_deletion_jobs",
    )
    op.drop_index(
        "ix_account_deletion_jobs_status",
        table_name="account_deletion_jobs",
    )
    op.drop_index(
        "ix_account_deletion_jobs_user_id",
        table_name="account_deletion_jobs",
    )
    op.drop_table("account_deletion_jobs")

    # 3. Drop auth_sessions table
    op.drop_index("ix_auth_sessions_user_status", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_provider_jti", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    # 2. Drop identity_accounts table
    op.drop_index(
        "ix_identity_accounts_user_id",
        table_name="identity_accounts",
    )
    op.drop_table("identity_accounts")

    # 1. Drop users lifecycle fields
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "deletion_requested_at")
    op.drop_column("users", "disabled_at")
    op.drop_column("users", "activated_at")
    op.drop_column("users", "email_verified")
    op.drop_index("ix_users_email_normalized", table_name="users")
    op.drop_column("users", "email_normalized")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_column("users", "status")
