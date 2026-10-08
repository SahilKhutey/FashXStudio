from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from schemas.journey.mvp import MvpJourneyGate, MvpJourneyStage, MvpJourneyState


@dataclass(frozen=True)
class JourneyInputs:
    user_id: UUID
    profile_ready: bool = False
    tryon_photo_ready: bool = False
    garment_selected: bool = False
    tryon_running: bool = False
    tryon_completed: bool = False
    decision_made: bool = False
    validation_captured: bool = False


def derive_stage(inputs: JourneyInputs) -> MvpJourneyState:
    if inputs.validation_captured:
        stage = MvpJourneyStage.VALIDATION_CAPTURED
    elif inputs.decision_made:
        stage = MvpJourneyStage.DECISION_PENDING
    elif inputs.tryon_completed:
        stage = MvpJourneyStage.TRYON_COMPLETED
    elif inputs.tryon_running:
        stage = MvpJourneyStage.TRYON_RUNNING
    elif inputs.garment_selected:
        stage = MvpJourneyStage.GARMENT_SELECTED
    elif inputs.tryon_photo_ready:
        stage = MvpJourneyStage.PHOTO_READY
    elif inputs.profile_ready:
        stage = MvpJourneyStage.PROFILE_READY
    else:
        stage = MvpJourneyStage.PROFILE_INCOMPLETE

    return MvpJourneyState(
        user_id=inputs.user_id,
        stage=stage,
        profile_ready=inputs.profile_ready,
        tryon_photo_ready=inputs.tryon_photo_ready,
        garment_selected=inputs.garment_selected,
        tryon_running=inputs.tryon_running,
        tryon_completed=inputs.tryon_completed,
        decision_made=inputs.decision_made,
        validation_captured=inputs.validation_captured,
    )


def can_start_tryon(inputs: JourneyInputs) -> MvpJourneyGate:
    if not inputs.profile_ready:
        return MvpJourneyGate(
            allowed=False,
            stage=MvpJourneyStage.PROFILE_INCOMPLETE,
            reason="profile_not_ready",
        )
    if not inputs.tryon_photo_ready:
        return MvpJourneyGate(
            allowed=False,
            stage=MvpJourneyStage.PROFILE_READY,
            reason="tryon_photo_not_ready",
        )
    if not inputs.garment_selected:
        return MvpJourneyGate(
            allowed=False,
            stage=MvpJourneyStage.PHOTO_READY,
            reason="garment_not_selected",
        )
    return MvpJourneyGate(allowed=True, stage=MvpJourneyStage.GARMENT_SELECTED)


def can_capture_validation(inputs: JourneyInputs) -> MvpJourneyGate:
    if not inputs.tryon_completed:
        return MvpJourneyGate(
            allowed=False,
            stage=derive_stage(inputs).stage,
            reason="tryon_not_completed",
        )
    return MvpJourneyGate(allowed=True, stage=MvpJourneyStage.TRYON_COMPLETED)
