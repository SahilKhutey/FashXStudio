from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MvpJourneyStage(StrEnum):
    PROFILE_INCOMPLETE = "profile_incomplete"
    PROFILE_READY = "profile_ready"
    PHOTO_PROCESSING = "photo_processing"
    PHOTO_READY = "photo_ready"
    GARMENT_SELECTED = "garment_selected"
    TRYON_RUNNING = "tryon_running"
    TRYON_COMPLETED = "tryon_completed"
    DECISION_PENDING = "decision_pending"
    VALIDATION_CAPTURED = "validation_captured"


class MvpJourneyState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    stage: MvpJourneyStage
    profile_ready: bool = False
    tryon_photo_ready: bool = False
    garment_selected: bool = False
    tryon_running: bool = False
    tryon_completed: bool = False
    decision_made: bool = False
    validation_captured: bool = False


class MvpJourneyGate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    stage: MvpJourneyStage
    reason: str | None = None
