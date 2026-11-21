from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class ImageOperation(StrEnum):
    FETCH = "IMAGE_FETCH"
    STORE = "IMAGE_STORE"
    DISPLAY = "IMAGE_DISPLAY"
    AI_PROCESS = "IMAGE_AI_PROCESS"
    VTO = "VTO_PROCESS"
    DERIVATIVE_CREATE = "DERIVATIVE_CREATE"
    DERIVATIVE_STORE = "DERIVATIVE_STORE"
    DERIVATIVE_DISPLAY = "DERIVATIVE_DISPLAY"


class ImageAssetStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETION_FAILED = "DELETION_FAILED"
    DELETED = "DELETED"
    REJECTED = "REJECTED"


class TransformationType(StrEnum):
    DISPLAY_THUMBNAIL = "DISPLAY_THUMBNAIL"
    DISPLAY_CARD = "DISPLAY_CARD"
    DISPLAY_DETAIL = "DISPLAY_DETAIL"
    VTO_INPUT = "VTO_INPUT"
    OTHER_AUTHORIZED = "OTHER_AUTHORIZED"


class QualityScore(StrEnum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    REJECT = "REJECT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    source_id: UUID
    evidence_id: UUID | None = None
    revision: int | None = None
    policy_version: str = "v1"
    reason: str | None = None


@dataclass(frozen=True)
class InspectedImage:
    original_bytes: bytes
    original_sha256: str
    normalized_bytes: bytes
    normalized_sha256: str
    detected_format: str
    mime_type: str
    width: int
    height: int
    byte_size: int
    perceptual_hash: str | None = None
    is_animated: bool = False


@dataclass(frozen=True)
class ImageQualityResult:
    score: QualityScore
    profile_name: str
    passed: bool
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedDerivative:
    transformation_type: TransformationType
    version: str
    processor_name: str
    processor_version: str | None
    data: bytes
    format: str
    mime_type: str
    width: int
    height: int
    byte_size: int
    sha256: str


@dataclass(frozen=True)
class ImageJobRequest:
    source_id: UUID
    merchant_id: UUID
    source_product_id: str
    image_url: str
    category: str
    source_variant_id: str | None = None
    canonical_garment_id: UUID | None = None
    correlation_id: str | None = None


@dataclass
class ImageJobResult:
    success: bool
    asset_id: UUID | None = None
    status: str = "PENDING"
    original_storage_key: str | None = None
    transformations: list[str] = field(default_factory=list)
    quality_score: str | None = None
    error_code: str | None = None
    error_message: str | None = None
