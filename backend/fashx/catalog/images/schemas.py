from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImageJobCreateRequest(BaseModel):
    source_id: UUID
    merchant_id: UUID
    source_product_id: str = Field(..., max_length=255)
    image_url: str = Field(..., min_length=5)
    category: str = Field(..., max_length=64)
    source_variant_id: str | None = Field(default=None, max_length=255)
    canonical_garment_id: UUID | None = None


class ImageJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    asset_id: UUID | None = None
    status: str
    original_storage_key: str | None = None
    transformations: list[str] = Field(default_factory=list)
    quality_score: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ImageAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    merchant_id: UUID
    source_product_id: str
    source_variant_id: str | None = None
    source_reference: str | None = None
    original_storage_key: str | None = None
    original_sha256: str | None = None
    normalized_sha256: str | None = None
    perceptual_hash: str | None = None
    original_mime_type: str | None = None
    original_width: int | None = None
    original_height: int | None = None
    original_bytes: int | None = None
    status: str
    quality_score: str | None = None
    quality_notes: dict | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ImageTransformationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    transformation_type: str
    transformation_version: str
    processor_name: str
    processor_version: str | None = None
    storage_key: str
    output_mime_type: str
    output_width: int
    output_height: int
    output_bytes: int
    output_sha256: str
    status: str
    created_at: datetime


class ImageTakedownCreateRequest(BaseModel):
    reason_code: str = Field(..., max_length=64)
    scope_type: str = Field(default="SOURCE", max_length=32)
    source_id: UUID | None = None
    merchant_id: UUID | None = None
    asset_id: UUID | None = None
    scope_target: str | None = None
    audit_metadata: dict = Field(default_factory=dict)


class ImageTakedownResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID | None = None
    merchant_id: UUID | None = None
    scope_type: str
    scope_target: str | None = None
    reason_code: str
    status: str
    audit_metadata: dict = Field(default_factory=dict)
    received_at: datetime
    completed_at: datetime | None = None
