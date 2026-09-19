from workers.profile_photo.pose.scoring import score_capture
from workers.profile_photo.pose.types import PoseEstimate


def test_tryon_capture_requires_reasonable_framing_and_detection():
    estimate = PoseEstimate(
        provider="test",
        provider_version="1",
        detected=True,
        landmark_count=0,
        mean_visibility=0.9,
        body_height_ratio=0.60,
        centeredness=0.95,
    )
    result = score_capture(estimate, photo_type="tryon_reference")
    assert 0.0 <= result.score <= 1.0
    assert result.ready_for_tryon is True


def test_missing_detection_is_rejected():
    estimate = PoseEstimate("test", "1", False, 0, 0.0)
    result = score_capture(estimate, photo_type="tryon_reference")
    assert result.ready_for_tryon is False
    assert result.reasons == ("person_not_detected",)


def test_weak_frame_is_not_tryon_ready():
    estimate = PoseEstimate("test", "1", True, 0, 0.4, body_height_ratio=0.20, centeredness=0.5)
    result = score_capture(estimate, photo_type="tryon_reference")
    assert result.ready_for_tryon is False
    assert "subject_small_in_frame" in result.reasons
