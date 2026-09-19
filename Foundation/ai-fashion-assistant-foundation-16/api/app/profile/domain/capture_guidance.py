from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID


REASON_COPY: dict[str, tuple[str, str]] = {
    "insufficient_resolution": (
        "Move closer or use a higher-resolution camera",
        "The image is too small for reliable body and garment alignment.",
    ),
    "unsupported_aspect_ratio": (
        "Use a portrait-oriented frame",
        "Keep your full body inside a normal portrait camera frame.",
    ),
    "invalid_image": (
        "Retake the photo",
        "The image could not be read correctly.",
    ),
    "face_not_detected": (
        "Keep your face visible",
        "Face the camera directly and remove anything covering your face.",
    ),
    "person_not_detected": (
        "Step into the camera frame",
        "Make sure your whole body is visible against a simple background.",
    ),
    "subject_small_in_frame": (
        "Step closer",
        "Your body is too small in the frame for reliable try-on alignment.",
    ),
    "subject_near_frame_edges": (
        "Move to the center",
        "Keep your body away from the left and right edges of the camera frame.",
    ),
    "landmark_pose_not_available": (
        "Keep a simple front-facing pose",
        "Stand upright with your arms slightly away from your body.",
    ),
    "capture_quality_below_threshold": (
        "Improve the camera position",
        "Use good lighting, a plain background, and keep your full body centered.",
    ),
}

DEFAULT_TIPS = [
    "Face the camera directly.",
    "Keep your full body visible from head to feet.",
    "Stand upright with your arms slightly away from your sides.",
    "Use even lighting and avoid strong backlight.",
    "Use a plain, uncluttered background.",
]


def build_capture_guidance(
    *,
    photo_id: UUID,
    status: str,
    ready_for_tryon: bool | None,
    quality_score: float | None,
    reasons: Sequence[str] | None,
) -> dict:
    reason_list = list(dict.fromkeys(reasons or []))

    if status in {"upload_pending", "processing"}:
        return {
            "state": "processing" if status == "processing" else "not_started",
            "ready_for_tryon": False,
            "title": "Checking your photo",
            "message": "We are validating the photo before it can be used for try-on.",
            "tips": DEFAULT_TIPS,
            "retryable": False,
            "quality_score": quality_score,
            "reasons": reason_list,
            "photo_id": photo_id,
        }

    if status == "accepted" and ready_for_tryon:
        return {
            "state": "ready",
            "ready_for_tryon": True,
            "title": "Photo ready",
            "message": "Your photo passed the capture checks and is ready for virtual try-on.",
            "tips": [],
            "retryable": False,
            "quality_score": quality_score,
            "reasons": reason_list,
            "photo_id": photo_id,
        }

    if status == "rejected":
        first = reason_list[0] if reason_list else "capture_quality_below_threshold"
        title, message = REASON_COPY.get(
            first,
            (
                "Retake your try-on photo",
                "The photo did not meet the quality requirements yet.",
            ),
        )
        return {
            "state": "retry",
            "ready_for_tryon": False,
            "title": title,
            "message": message,
            "tips": DEFAULT_TIPS,
            "retryable": True,
            "quality_score": quality_score,
            "reasons": reason_list,
            "photo_id": photo_id,
        }

    return {
        "state": "failed",
        "ready_for_tryon": False,
        "title": "Photo needs attention",
        "message": "The photo is not ready for try-on. Please capture a new photo.",
        "tips": DEFAULT_TIPS,
        "retryable": True,
        "quality_score": quality_score,
        "reasons": reason_list,
        "photo_id": photo_id,
    }
