from __future__ import annotations

from dataclasses import dataclass

from .types import PoseEstimate


@dataclass(frozen=True)
class CaptureQuality:
    score: float
    pose_score: float
    framing_score: float
    landmark_confidence: float
    ready_for_tryon: bool
    reasons: tuple[str, ...]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_capture(estimate: PoseEstimate, *, photo_type: str, threshold: float = 0.55) -> CaptureQuality:
    reasons: list[str] = []
    if not estimate.detected:
        return CaptureQuality(0.0, 0.0, 0.0, 0.0, False, ("person_not_detected",))

    landmark_conf = _clamp(estimate.mean_visibility)
    if estimate.landmark_count >= 20:
        pose_score = _clamp(landmark_conf)
    else:
        pose_score = _clamp(estimate.mean_visibility * 0.6)
        reasons.append("landmark_pose_not_available")

    body_ratio = estimate.body_height_ratio or 0.0
    framing_score = _clamp(estimate.centeredness or 0.0)
    if photo_type == "tryon_reference":
        if body_ratio < 0.35:
            framing_score *= 0.7
            reasons.append("subject_small_in_frame")
        if body_ratio > 0.95:
            framing_score *= 0.8
            reasons.append("subject_near_frame_edges")
        score = _clamp(0.55 * pose_score + 0.45 * framing_score)
        ready = score >= threshold and estimate.detected
    else:
        score = _clamp(0.7 * pose_score + 0.3 * framing_score)
        ready = score >= min(threshold, 0.45) and estimate.detected

    if not ready:
        reasons.append("capture_quality_below_threshold")
    return CaptureQuality(score, pose_score, framing_score, landmark_conf, ready, tuple(reasons))
