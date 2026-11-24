"""Common validation domain models and data contracts for Phase 07.3."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"


class ImageRole(str, Enum):
    SHOPPER = "SHOPPER"
    GARMENT = "GARMENT"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ValidationIssue(BaseModel):
    code: str
    severity: Severity
    message: str
    user_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TechnicalMetadata(BaseModel):
    width: int
    height: int
    format: str
    size_bytes: int
    original_sha256: str
    normalized_sha256: str


class VisualMetadata(BaseModel):
    person_detected: bool | None = None
    person_count: int | None = None
    visible_regions: list[str] = Field(default_factory=list)
    pose_label: str | None = None
    pose_confidence: float | None = None
    occlusion_detected: bool | None = None
    garment_visible: bool | None = None
    background_suitable: bool | None = None
    confidence: float | None = None
    model_name: str = "builtin-heuristic"
    model_version: str = "v1.0"


class ImageValidationResult(BaseModel):
    role: ImageRole
    status: ValidationStatus
    asset_id: str
    asset_version: str
    policy_version: str
    technical_metadata: TechnicalMetadata | None = None
    visual_metadata: VisualMetadata | None = None
    issues: list[ValidationIssue] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def can_proceed(self) -> bool:
        return self.status in (
            ValidationStatus.PASSED,
            ValidationStatus.PASSED_WITH_WARNINGS,
        )


class CombinedValidationResult(BaseModel):
    status: ValidationStatus
    shopper: ImageValidationResult
    garment: ImageValidationResult

    @property
    def can_submit(self) -> bool:
        return (
            self.shopper.can_proceed
            and self.garment.can_proceed
            and self.status in (
                ValidationStatus.PASSED,
                ValidationStatus.PASSED_WITH_WARNINGS,
            )
        )


class ValidationRequest(BaseModel):
    user_id: UUID
    shopper_asset_id: UUID
    product_id: UUID
    garment_category: str = "tops"
    offer_id: UUID | None = None
    garment_image_asset_id: UUID | None = None
    garment_image_version: str = "v1"
