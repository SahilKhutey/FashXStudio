from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class EnrichmentStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class EvidenceType(StrEnum):
    MERCHANT_FIELD = "MERCHANT_FIELD"
    TITLE = "TITLE"
    DESCRIPTION = "DESCRIPTION"
    IMAGE_ASSET = "IMAGE_ASSET"
    SOURCE_SPECIFICATION = "SOURCE_SPECIFICATION"
    RULE_MATCH = "RULE_MATCH"
    AI_TEXT_EXTRACTION = "AI_TEXT_EXTRACTION"
    AI_IMAGE_EXTRACTION = "AI_IMAGE_EXTRACTION"
    HUMAN_CORRECTION = "HUMAN_CORRECTION"


class ReviewStatus(StrEnum):
    AUTO_ACCEPTED = "AUTO_ACCEPTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"
    NOT_REQUIRED = "NOT_REQUIRED"


class AttributeStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_PROVIDED = "NOT_PROVIDED"


class AttributeSource(StrEnum):
    MERCHANT = "MERCHANT"
    RULE_BASED = "RULE_BASED"
    AI_TEXT = "AI_TEXT"
    AI_IMAGE = "AI_IMAGE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FALLBACK = "FALLBACK"


class ReviewFlag(StrEnum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INVALID_TAXONOMY_VALUE = "INVALID_TAXONOMY_VALUE"
    UNSUPPORTED_ATTRIBUTE = "UNSUPPORTED_ATTRIBUTE"
    SOURCE_DATA_INCOMPLETE = "SOURCE_DATA_INCOMPLETE"
    MODEL_OUTPUT_INVALID = "MODEL_OUTPUT_INVALID"
    FABRIC_UNVERIFIED = "FABRIC_UNVERIFIED"
    CATEGORY_AMBIGUOUS = "CATEGORY_AMBIGUOUS"


class EnrichmentPermissions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_processing: bool = True
    image_ai_processing: bool = False
    vto_processing: bool = False


class EnrichmentImageAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    asset_url: str | None = None
    image_type: str = "PRIMARY"
    has_ai_permission: bool = False


class ProductContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    merchant_category: str | None = None
    brand: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    variants: list[dict[str, Any]] = Field(default_factory=list)
    size_information: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Product title cannot be empty or whitespace only")
        return stripped


class EnrichmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    product_id: str
    merchant_id: str
    source_id: str
    source_product_id: str
    taxonomy_version: str
    content: ProductContent
    images: list[EnrichmentImageAsset] = Field(default_factory=list)
    permissions: EnrichmentPermissions = Field(default_factory=EnrichmentPermissions)
    source_revision: str | None = None

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("product_id cannot be empty")
        return v.strip()

    @field_validator("taxonomy_version")
    @classmethod
    def validate_taxonomy_version(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("taxonomy_version cannot be empty")
        return v.strip()

    @property
    def text_processing_allowed(self) -> bool:
        return self.permissions.text_processing

    @property
    def image_ai_processing_allowed(self) -> bool:
        return self.permissions.image_ai_processing


class EnrichmentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    evidence_type: EvidenceType
    source_record_id: str
    source_revision: str | None = None
    asset_id: str | None = None
    evidence_text: str | None = None
    evidence_hash: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    extraction_method: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AttributeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any | None = None
    status: AttributeStatus = AttributeStatus.KNOWN
    confidence: float | None = None
    source: AttributeSource | None = None
    review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED
    evidence_ids: list[str] = Field(default_factory=list)
    flags: list[ReviewFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_value_consistency(self) -> AttributeResult:
        if self.status == AttributeStatus.KNOWN:
            if self.value is None:
                raise ValueError("Attribute with status KNOWN must provide a non-null value")
        elif self.status in {
            AttributeStatus.UNKNOWN,
            AttributeStatus.NOT_PROVIDED,
            AttributeStatus.NOT_APPLICABLE,
        }:
            if self.value is not None:
                raise ValueError(
                    f"Attribute with status {self.status.value} must have a null value"
                )

        if self.confidence is not None and self.source is None:
            raise ValueError("Confidence score requires an attribute source")

        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError("Confidence score must be between 0.0 and 1.0")

        return self


class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required: bool = False
    reasons: list[str] = Field(default_factory=list)


class EnrichmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    product_id: str
    taxonomy_version: str
    enrichment_version: str = "1.0.0"
    status: EnrichmentStatus
    category_id: str | None = None
    garment_type: str | None = None
    attributes: dict[str, AttributeResult] = Field(default_factory=dict)
    evidence: list[EnrichmentEvidence] = Field(default_factory=list)
    review: ReviewSummary = Field(default_factory=ReviewSummary)
    idempotency_key: str | None = None
