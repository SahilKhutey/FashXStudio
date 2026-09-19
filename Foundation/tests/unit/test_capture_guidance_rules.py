from uuid import uuid4

from api.app.profile.domain.capture_guidance import build_capture_guidance


def test_processing_guidance():
    result = build_capture_guidance(
        photo_id=uuid4(),
        status="processing",
        ready_for_tryon=None,
        quality_score=None,
        reasons=[],
    )
    assert result["state"] == "processing"
    assert result["retryable"] is False


def test_ready_guidance():
    result = build_capture_guidance(
        photo_id=uuid4(),
        status="accepted",
        ready_for_tryon=True,
        quality_score=0.91,
        reasons=[],
    )
    assert result["state"] == "ready"
    assert result["ready_for_tryon"] is True


def test_retry_guidance_is_specific():
    result = build_capture_guidance(
        photo_id=uuid4(),
        status="rejected",
        ready_for_tryon=False,
        quality_score=0.3,
        reasons=["subject_small_in_frame", "capture_quality_below_threshold"],
    )
    assert result["state"] == "retry"
    assert result["title"] == "Step closer"
    assert result["retryable"] is True
    assert result["tips"]
