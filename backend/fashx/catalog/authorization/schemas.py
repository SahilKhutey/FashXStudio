from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.models.catalog_auth import (
    CatalogPermissionCode,
    EvidenceVerificationStatus,
)


class AuthorizationContext(BaseModel):
    source_id: UUID
    operation: str = Field(
        ..., description="CatalogPermissionCode e.g. PRODUCT_DATA_READ, IMAGE_AI_PROCESS"
    )
    product_id: str | None = None
    category: str | None = None
    market: str | None = None
    processor_id: str | None = None
    correlation_id: str | None = None


class AuthorizationDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision: str  # ALLOW | DENY
    reason_code: str
    source_id: UUID
    product_id: str | None = None
    operation: str
    permission_id: UUID | None = None
    evaluated_at: datetime


class EvidenceCreate(BaseModel):
    source_id: UUID
    evidence_type: str = Field(default="CONTRACT", max_length=32)
    document_reference: str = Field(..., min_length=2, max_length=512)
    document_sha256: str | None = Field(default=None, max_length=64)
    agreement_reference: str | None = Field(default=None, max_length=255)
    agreement_version: str | None = Field(default=None, max_length=100)
    granted_by_name: str | None = Field(default=None, max_length=255)
    granted_by_role: str | None = Field(default=None, max_length=160)
    verified_by: UUID | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.VERIFIED


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    evidence_type: str
    document_reference: str
    document_sha256: str | None = None
    agreement_reference: str | None = None
    agreement_version: str | None = None
    granted_by_name: str | None = None
    granted_by_role: str | None = None
    verified_by: UUID | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    verification_status: str
    created_at: datetime


class PermissionCreate(BaseModel):
    source_id: UUID
    permission_code: CatalogPermissionCode
    granted_by: str = Field(..., min_length=1, max_length=255)
    evidence_id: UUID | None = None
    scope_categories: list[str] = Field(default_factory=list)
    scope_markets: list[str] = Field(default_factory=list)
    processor_restrictions: list[str] = Field(default_factory=list)
    storage_limit_days: int | None = Field(default=None, ge=1)
    effective_at: datetime | None = None
    expires_at: datetime | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    permission_code: str
    permission_status: str
    granted_by: str
    evidence_id: UUID | None = None
    scope_categories: list[str] = []
    scope_markets: list[str] = []
    processor_restrictions: list[str] = []
    storage_limit_days: int | None = None
    effective_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime


class DecisionAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    product_id: str | None = None
    operation: str
    decision: str
    reason_code: str
    permission_id: UUID | None = None
    processor_id: str | None = None
    market: str | None = None
    category: str | None = None
    correlation_id: str | None = None
    evaluated_at: datetime
