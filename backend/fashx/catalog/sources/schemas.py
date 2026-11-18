from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.models.catalog_auth import (
    CatalogAccessMethod,
    CatalogSourceStatus,
    CatalogSourceType,
)


class SourceCreate(BaseModel):
    merchant_id: UUID
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    source_name: str | None = Field(default=None, max_length=160)
    source_type: CatalogSourceType = CatalogSourceType.MERCHANT_API
    source_owner: str | None = Field(default=None, max_length=255)
    provider_name: str | None = Field(default=None, max_length=100)
    source_description: str | None = None
    access_method: CatalogAccessMethod = CatalogAccessMethod.API_KEY
    credential_secret_ref: str | None = Field(default=None, max_length=512)
    market_codes: list[str] = Field(default_factory=lambda: ["IN"])
    category_codes: list[str] = Field(default_factory=lambda: ["apparel"])
    refresh_hours: int = Field(default=24, ge=1, le=720)
    max_rps: float = Field(default=2.0, gt=0, le=100.0)
    terms_url: str | None = None
    takedown_contact: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    next_review_at: datetime | None = None


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    source_name: str | None = Field(default=None, max_length=160)
    source_owner: str | None = Field(default=None, max_length=255)
    provider_name: str | None = Field(default=None, max_length=100)
    source_description: str | None = None
    access_method: CatalogAccessMethod | None = None
    credential_secret_ref: str | None = Field(default=None, max_length=512)
    market_codes: list[str] | None = None
    category_codes: list[str] | None = None
    refresh_hours: int | None = Field(default=None, ge=1, le=720)
    max_rps: float | None = Field(default=None, gt=0, le=100.0)
    terms_url: str | None = None
    takedown_contact: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    next_review_at: datetime | None = None


class SourceStatusUpdate(BaseModel):
    target_status: CatalogSourceStatus
    reason: str = Field(..., min_length=3, max_length=500)
    reviewer_id: UUID | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID | None = None
    slug: str
    name: str
    source_name: str | None = None
    source_type: str | None = None
    source_owner: str | None = None
    provider_name: str | None = None
    source_description: str | None = None
    access_method: str | None = None
    credential_secret_ref: str | None = None
    source_status: str
    market_codes: list[str] = []
    category_codes: list[str] = []
    refresh_hours: int
    max_rps: float
    terms_url: str | None = None
    takedown_contact: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    next_review_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    last_authorization_check_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
