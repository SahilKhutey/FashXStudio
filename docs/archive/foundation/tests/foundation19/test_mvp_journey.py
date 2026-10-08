from uuid import uuid4

from api.app.journey.domain.state import JourneyInputs, can_capture_validation, can_start_tryon, derive_stage
from schemas.journey.mvp import MvpJourneyStage


def test_new_user_is_profile_incomplete():
    user_id = uuid4()
    state = derive_stage(JourneyInputs(user_id=user_id))
    assert state.stage == MvpJourneyStage.PROFILE_INCOMPLETE
    assert not state.profile_ready


def test_profile_ready_stage():
    state = derive_stage(JourneyInputs(user_id=uuid4(), profile_ready=True))
    assert state.stage == MvpJourneyStage.PROFILE_READY


def test_photo_ready_stage():
    state = derive_stage(
        JourneyInputs(user_id=uuid4(), profile_ready=True, tryon_photo_ready=True)
    )
    assert state.stage == MvpJourneyStage.PHOTO_READY


def test_tryon_gate_requires_profile():
    gate = can_start_tryon(
        JourneyInputs(user_id=uuid4(), tryon_photo_ready=True, garment_selected=True)
    )
    assert not gate.allowed
    assert gate.reason == "profile_not_ready"


def test_tryon_gate_requires_photo():
    gate = can_start_tryon(JourneyInputs(user_id=uuid4(), profile_ready=True, garment_selected=True))
    assert not gate.allowed
    assert gate.reason == "tryon_photo_not_ready"


def test_tryon_gate_requires_garment():
    gate = can_start_tryon(
        JourneyInputs(user_id=uuid4(), profile_ready=True, tryon_photo_ready=True)
    )
    assert not gate.allowed
    assert gate.reason == "garment_not_selected"


def test_tryon_gate_allows_start_when_prerequisites_are_ready():
    gate = can_start_tryon(
        JourneyInputs(
            user_id=uuid4(), profile_ready=True, tryon_photo_ready=True, garment_selected=True
        )
    )
    assert gate.allowed
    assert gate.stage == MvpJourneyStage.GARMENT_SELECTED


def test_tryon_completed_stage():
    state = derive_stage(
        JourneyInputs(
            user_id=uuid4(),
            profile_ready=True,
            tryon_photo_ready=True,
            garment_selected=True,
            tryon_completed=True,
        )
    )
    assert state.stage == MvpJourneyStage.TRYON_COMPLETED


def test_validation_requires_completed_tryon():
    gate = can_capture_validation(
        JourneyInputs(user_id=uuid4(), profile_ready=True, tryon_photo_ready=True)
    )
    assert not gate.allowed
    assert gate.reason == "tryon_not_completed"


def test_validation_can_start_after_completed_tryon():
    gate = can_capture_validation(JourneyInputs(user_id=uuid4(), tryon_completed=True))
    assert gate.allowed
    assert gate.stage == MvpJourneyStage.TRYON_COMPLETED


def test_terminal_validation_stage_has_priority():
    state = derive_stage(
        JourneyInputs(
            user_id=uuid4(),
            profile_ready=True,
            tryon_photo_ready=True,
            garment_selected=True,
            tryon_completed=True,
            decision_made=True,
            validation_captured=True,
        )
    )
    assert state.stage == MvpJourneyStage.VALIDATION_CAPTURED
