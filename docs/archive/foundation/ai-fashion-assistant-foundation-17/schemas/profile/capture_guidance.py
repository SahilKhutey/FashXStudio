from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class CaptureGuidanceState(StrEnum):
    READY = "ready"
    PROCESSING = "processing"
    RETRY = "retry"
    NOT_STARTED = "not_started"
    FAILED = "failed"


class CaptureGuidanceResponse(BaseModel):
    state: CaptureGuidanceState
    ready_for_tryon: bool
    title: str
    message: str
    tips: list[str] = Field(default_factory=list)
    retryable: bool
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    photo_id: UUID
