from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SkinToneResult(BaseModel):
    result_id: UUID
    photo_id: UUID
    ita_degrees: float | None = None
    tone_class: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    method: str
    model_version: str
    status: str
    created_at: datetime


class ProfileReadiness(BaseModel):
    profile_version: int
    body_profile_complete: bool
    tryon_photo_ready: bool
    skin_tone_ready: bool
    ready_for_tryon: bool
    missing: list[str] = Field(default_factory=list)


class ProfileArtifactResponse(BaseModel):
    artifact_id: UUID
    user_id: UUID
    version: int
    body: dict[str, object]
    preferences: dict[str, object]
    tryon_photo_id: UUID | None = None
    skin_tone: SkinToneResult | None = None
    ready_for_tryon: bool
    created_at: datetime
