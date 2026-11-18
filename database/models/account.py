from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin
from .identity import User


class IdentityAccount(Base, UUIDPrimaryKeyMixin):
    """Links an external identity provider account (Cognito, Apple, Google) to internal User."""

    __tablename__ = "identity_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_subject", name="uq_identity_accounts_provider_subject"
        ),
        UniqueConstraint("user_id", "provider", name="uq_identity_accounts_user_provider"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship()


class AuthSession(Base, UUIDPrimaryKeyMixin):
    """Tracks active authenticated client sessions for device awareness and selective revocation."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint("provider", "provider_jti", name="uq_auth_sessions_provider_jti"),
        Index("ix_auth_sessions_user_status", "user_id", "session_status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_origin_jti: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_jti: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship()


class AccountDeletionJob(Base, UUIDPrimaryKeyMixin):
    """Durable asynchronous account deletion tracking record. Retained post-erasure as audit record."""

    __tablename__ = "account_deletion_jobs"
    __table_args__ = (Index("ix_account_deletion_jobs_user_status", "user_id", "status"),)

    user_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", server_default="PENDING", nullable=False, index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    max_attempts: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5", nullable=False
    )
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
