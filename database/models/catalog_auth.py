from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .catalog import CatalogSource


class MerchantVerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class CatalogSourceType(StrEnum):
    MERCHANT_API = "MERCHANT_API"
    AFFILIATE_API = "AFFILIATE_API"
    MERCHANT_FEED = "MERCHANT_FEED"
    PARTNER_EXPORT = "PARTNER_EXPORT"
    SHOPIFY_APP = "SHOPIFY_APP"
    OTHER_AUTHORIZED = "OTHER_AUTHORIZED"


class CatalogAccessMethod(StrEnum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    SIGNED_REQUEST = "SIGNED_REQUEST"
    WEBHOOK = "WEBHOOK"
    SFTP = "SFTP"
    HTTPS_FEED = "HTTPS_FEED"
    MANUAL_PARTNER_EXPORT = "MANUAL_PARTNER_EXPORT"
    OTHER = "OTHER"


class CatalogSourceStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


class CatalogPermissionCode(StrEnum):
    PRODUCT_DATA_READ = "PRODUCT_DATA_READ"
    PRODUCT_DATA_STORE = "PRODUCT_DATA_STORE"
    PRODUCT_DISPLAY = "PRODUCT_DISPLAY"
    IMAGE_FETCH = "IMAGE_FETCH"
    IMAGE_DISPLAY = "IMAGE_DISPLAY"
    IMAGE_STORE = "IMAGE_STORE"
    IMAGE_AI_PROCESS = "IMAGE_AI_PROCESS"
    VTO_PROCESS = "VTO_PROCESS"
    DERIVATIVE_CREATE = "DERIVATIVE_CREATE"
    DERIVATIVE_STORE = "DERIVATIVE_STORE"
    DERIVATIVE_DISPLAY = "DERIVATIVE_DISPLAY"
    MERCHANT_REDIRECT = "MERCHANT_REDIRECT"
    AFFILIATE_ATTRIBUTION = "AFFILIATE_ATTRIBUTION"


class CatalogPermissionStatus(StrEnum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class EvidenceVerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class TakedownReasonCode(StrEnum):
    MERCHANT_REQUEST = "MERCHANT_REQUEST"
    LICENSE_EXPIRED = "LICENSE_EXPIRED"
    LICENSE_REVOKED = "LICENSE_REVOKED"
    IMAGE_RIGHTS_DISPUTE = "IMAGE_RIGHTS_DISPUTE"
    DATA_RIGHTS_DISPUTE = "DATA_RIGHTS_DISPUTE"
    PROVIDER_TERMINATION = "PROVIDER_TERMINATION"
    CREDENTIAL_COMPROMISE = "CREDENTIAL_COMPROMISE"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    INCORRECT_PRODUCT_DATA = "INCORRECT_PRODUCT_DATA"
    LEGAL_REQUEST = "LEGAL_REQUEST"
    OTHER = "OTHER"


class TakedownStatus(StrEnum):
    RECEIVED = "RECEIVED"
    TRIAGED = "TRIAGED"
    SUSPENDED = "SUSPENDED"
    PROCESSING = "PROCESSING"
    VERIFICATION = "VERIFICATION"
    COMPLETED = "COMPLETED"
    EXCEPTION = "EXCEPTION"


class CatalogAuthorizationEvidence(Base, UUIDPrimaryKeyMixin):
    """Stores verified contractual and legal authorization references."""

    __tablename__ = "catalog_authorization_evidence"
    __table_args__ = (
        Index("ix_catalog_auth_evidence_source", "source_id"),
        Index("ix_catalog_auth_evidence_status", "verification_status"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    document_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agreement_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agreement_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    granted_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    granted_by_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(24),
        default=EvidenceVerificationStatus.PENDING.value,
        server_default=EvidenceVerificationStatus.PENDING.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[CatalogSource] = relationship(back_populates="evidence_records")
    permissions: Mapped[list[CatalogSourcePermission]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan"
    )


class CatalogSourcePermission(Base, UUIDPrimaryKeyMixin):
    """Append-only permission records granting granular catalog operations."""

    __tablename__ = "catalog_source_permissions"
    __table_args__ = (
        Index("idx_source_permissions_source", "source_id"),
        Index("idx_source_permissions_code", "permission_code"),
        Index("idx_source_permissions_expiry", "expires_at"),
        Index("idx_source_permissions_lookup", "source_id", "permission_code", "permission_status"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    permission_code: Mapped[str] = mapped_column(String(48), nullable=False)
    permission_status: Mapped[str] = mapped_column(
        String(16),
        default=CatalogPermissionStatus.GRANTED.value,
        server_default=CatalogPermissionStatus.GRANTED.value,
        nullable=False,
    )
    granted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_authorization_evidence.id", ondelete="SET NULL"), nullable=True
    )
    scope_categories: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    scope_markets: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    processor_restrictions: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    storage_limit_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[CatalogSource] = relationship(back_populates="permissions")
    evidence: Mapped[CatalogAuthorizationEvidence | None] = relationship(
        back_populates="permissions"
    )


class CatalogTakedownRequest(Base, UUIDPrimaryKeyMixin):
    """Formal audit record of takedown and suspension procedures."""

    __tablename__ = "catalog_takedown_requests"
    __table_args__ = (
        Index("ix_catalog_takedown_source", "source_id"),
        Index("ix_catalog_takedown_status", "status"),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(48), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    request_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        String(24),
        default=TakedownStatus.RECEIVED.value,
        server_default=TakedownStatus.RECEIVED.value,
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    affected_product_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    affected_asset_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    assigned_reviewer: Mapped[UUID | None] = mapped_column(nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[CatalogSource] = relationship(back_populates="takedowns")


class CatalogAuthorizationDecision(Base, UUIDPrimaryKeyMixin):
    """Audit event log for every authorization engine decision."""

    __tablename__ = "catalog_authorization_decisions"
    __table_args__ = (
        Index("ix_catalog_auth_decision_source", "source_id"),
        Index("ix_catalog_auth_decision_time", "evaluated_at"),
        Index("ix_catalog_auth_decision_decision", "decision"),
    )

    source_id: Mapped[UUID] = mapped_column(nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operation: Mapped[str] = mapped_column(String(48), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # ALLOW | DENY
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    permission_id: Mapped[UUID | None] = mapped_column(nullable=True)
    processor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    market: Mapped[str | None] = mapped_column(String(16), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
