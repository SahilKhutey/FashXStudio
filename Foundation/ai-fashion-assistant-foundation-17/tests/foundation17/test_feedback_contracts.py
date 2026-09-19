from uuid import uuid4
from pydantic import ValidationError

from schemas.common.enums import VisualAccuracy
from schemas.feedback.visual import TryOnFeedbackCreate
from schemas.tryon.telemetry import TryOnTelemetryCreate, TryOnTelemetryEvent


def test_visual_feedback_contract_accepts_bounded_confidence() -> None:
    job_id = uuid4()
    payload = TryOnFeedbackCreate(
        tryon_job_id=job_id,
        visual_accuracy=VisualAccuracy.ACCURATE,
        purchase_confidence=5,
    )
    assert payload.tryon_job_id == job_id
    assert payload.purchase_confidence == 5


def test_visual_feedback_rejects_confidence_outside_scale() -> None:
    try:
        TryOnFeedbackCreate(
            tryon_job_id=uuid4(),
            visual_accuracy=VisualAccuracy.NEUTRAL,
            purchase_confidence=6,
        )
    except ValidationError:
        return
    raise AssertionError("purchase confidence must be limited to 1..5")


def test_tryon_telemetry_contract_is_allowlisted() -> None:
    payload = TryOnTelemetryCreate(event=TryOnTelemetryEvent.VIEWED, elapsed_ms=4200, screen_context="result")
    assert payload.event.value == "viewed"
    assert payload.elapsed_ms == 4200
