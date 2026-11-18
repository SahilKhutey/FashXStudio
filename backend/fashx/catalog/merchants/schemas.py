from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.models.catalog_auth import MerchantVerificationStatus


class MerchantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    merchant_type: str = Field(default="brand", min_length=1, max_length=64)
    legal_name: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    country_code: str = Field(default="IN", min_length=2, max_length=8)
    registration_reference: str | None = Field(default=None, max_length=128)
    primary_contact_id: UUID | None = None
    technical_contact_id: UUID | None = None
    takedown_contact_id: UUID | None = None


class MerchantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    merchant_type: str | None = Field(default=None, min_length=1, max_length=64)
    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, min_length=2, max_length=8)
    registration_reference: str | None = Field(default=None, max_length=128)
    primary_contact_id: UUID | None = None
    technical_contact_id: UUID | None = None
    takedown_contact_id: UUID | None = None


class MerchantVerificationRequest(BaseModel):
    verification_status: MerchantVerificationStatus
    reason: str = Field(..., min_length=3, max_length=500)
    reviewer_id: UUID | None = None


class MerchantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    merchant_type: str
    legal_name: str | None = None
    display_name: str | None = None
    website: str | None = None
    country_code: str
    registration_reference: str | None = None
    verification_status: str
    primary_contact_id: UUID | None = None
    technical_contact_id: UUID | None = None
    takedown_contact_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
