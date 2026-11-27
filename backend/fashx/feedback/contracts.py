"""Versioned Pydantic request and response contracts for Phase 08.5."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from fashx.feedback.enums import ConsentPurpose, ReactionState, VTOQualityRating


class FeedbackEventRequest(BaseModel):
    """Client-submitted interaction or feedback event (shopper identity from auth)."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: str = Field(min_length=1, max_length=80)
    subject_type: str = Field(min_length=1, max_length=40)
    subject_id: str = Field(min_length=1, max_length=128)
    occurred_at: datetime
    schema_version: int = Field(default=1, ge=1)
    source: str = Field(default="mobile", min_length=1, max_length=32)
    session_id: str | None = Field(default=None, max_length=128)
    context: dict[str, Any] = Field(default_factory=dict)


class FeedbackEventResponse(BaseModel):
    event_id: UUID
    status: str
    received_at: datetime
    deduplicated: bool = False


class ReactionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reaction: ReactionState
    idempotency_key: UUID


class ReactionResponse(BaseModel):
    product_id: str
    reaction: ReactionState
    status: str = "RECORDED"


class SaveProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: UUID
    merchant_offer_id: str | None = Field(default=None, max_length=128)


class SavedProductResponse(BaseModel):
    product_id: str
    merchant_offer_id: str | None = None
    is_saved: bool
    saved_at: datetime | None = None
    updated_at: datetime


class VTOQualityFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID | None = None
    rating: VTOQualityRating
    issue_codes: list[str] = Field(default_factory=list)
    comment: str | None = Field(default=None, max_length=1000)


class VTOQualityFeedbackResponse(BaseModel):
    job_id: str
    rating: VTOQualityRating
    issue_codes: list[str]
    status: str = "RECORDED"


class OutboundClickRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID | None = None
    product_id: str = Field(min_length=1, max_length=128)
    source: str = Field(default="PRODUCT_DETAIL", min_length=1, max_length=40)


class OutboundClickResponse(BaseModel):
    redirect_id: str
    merchant_offer_id: str
    product_id: str
    recorded: bool = True


class ConsentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    granted: bool
    policy_version: str = Field(default="2026.1", min_length=1, max_length=32)
    source: str = Field(default="app", min_length=1, max_length=32)


class ConsentStateResponse(BaseModel):
    purpose: ConsentPurpose
    status: str
    policy_version: str
    revision: int
    recorded_at: datetime
    withdrawn_at: datetime | None = None
