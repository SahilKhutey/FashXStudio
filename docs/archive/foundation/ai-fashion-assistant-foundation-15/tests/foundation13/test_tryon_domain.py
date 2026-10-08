from uuid import UUID

from api.app.tryon.domain.artifact import compute_artifact_key
from api.app.tryon.domain.state_machine import can_transition


def test_artifact_key_changes_with_model_version() -> None:
    photo = UUID("00000000-0000-0000-0000-000000000001")
    garment = UUID("00000000-0000-0000-0000-000000000002")
    a = compute_artifact_key(photo_id=photo, photo_version=1, garment_id=garment, garment_version=1, model_version="v1", pipeline_version="p1")
    b = compute_artifact_key(photo_id=photo, photo_version=1, garment_id=garment, garment_version=1, model_version="v2", pipeline_version="p1")
    assert a != b


def test_completed_has_no_forward_transition() -> None:
    assert not can_transition("completed", "inference")


def test_queued_can_enter_validation() -> None:
    assert can_transition("queued", "validating")
