from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    product_id: UUID
    status: str
    message: str = "Enrichment job queued"


class EnrichmentRunStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    product_id: UUID
    status: str
    attempt_number: int
    started_at: datetime
    completed_at: datetime | None = None
    error_code: str | None = None


class EnrichmentResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    taxonomy_version: str
    enrichment_version: str
    status: str
    category_id: str | None = None
    garment_type: str | None = None
    summary_json: dict[str, Any]
    is_current: bool
    created_at: datetime


class ReviewItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    product_id: UUID
    merchant_id: UUID
    attribute_id: str
    proposed_value: str | None = None
    current_value: str | None = None
    status: str
    confidence: float | None = None
    flags: list[str] = Field(default_factory=list)
    reason: str | None = None
    created_at: datetime


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str  # APPROVE, CORRECT, REJECT, MARK_UNKNOWN
    corrected_value: str | None = None
    reason: str = "Decision recorded by reviewer"


class ReviewDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: UUID
    status: str
    attribute_id: str
    current_value: str | None = None
    reviewed_by: str
    reviewed_at: datetime
