from __future__ import annotations

from pydantic import BaseModel, Field


class CaptureQuality(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    pose_score: float = Field(ge=0.0, le=1.0)
    framing_score: float = Field(ge=0.0, le=1.0)
    landmark_confidence: float = Field(ge=0.0, le=1.0)
    ready_for_tryon: bool
    provider: str
    provider_version: str
    reasons: list[str] = Field(default_factory=list)
