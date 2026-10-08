from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from api.app.core.settings import get_settings
from workers.profile_photo.pose.heuristic import HeuristicPoseEstimator
from workers.profile_photo.pose.mediapipe_adapter import MediaPipePoseEstimator
from workers.profile_photo.pose.scoring import CaptureQuality, score_capture
from workers.profile_photo.pose.types import PoseEstimate


@dataclass(frozen=True)
class PhotoValidationResult:
    accepted: bool
    reason: str | None
    content_sha256: str
    width: int
    height: int
    image_format: str
    mode: str
    has_person: bool | None = None
    has_face: bool | None = None
    capture_quality: CaptureQuality | None = None
    pose_estimate: PoseEstimate | None = None


class PhotoValidationError(ValueError):
    pass


class BasicPhotoValidator:
    MIN_WIDTH = 512
    MIN_HEIGHT = 512
    MAX_ASPECT_RATIO = 2.5

    def __init__(self, pose_estimator=None, *, quality_threshold: float | None = None) -> None:
        settings = get_settings()
        if pose_estimator is not None:
            self.pose_estimator = pose_estimator
        elif settings.pose_provider == "mediapipe":
            self.pose_estimator = MediaPipePoseEstimator(model_path=settings.pose_model_path or "")
        elif settings.pose_provider == "opencv_heuristic":
            self.pose_estimator = HeuristicPoseEstimator()
        else:
            raise ValueError(f"Unsupported POSE_PROVIDER: {settings.pose_provider}")
        self.quality_threshold = quality_threshold if quality_threshold is not None else settings.capture_quality_threshold
        self._face = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def validate(self, payload: bytes, *, photo_type: str) -> PhotoValidationResult:
        digest = sha256(payload).hexdigest()
        try:
            with Image.open(BytesIO(payload)) as image:
                image.verify()
            with Image.open(BytesIO(payload)) as image:
                normalized = ImageOps.exif_transpose(image)
                width, height = normalized.size
                image_format = (normalized.format or image.format or "unknown").lower()
                mode = normalized.mode
                if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                    return PhotoValidationResult(False, "insufficient_resolution", digest, width, height, image_format, mode)
                ratio = max(width / height, height / width)
                if ratio > self.MAX_ASPECT_RATIO:
                    return PhotoValidationResult(False, "unsupported_aspect_ratio", digest, width, height, image_format, mode)
                if image_format not in {"jpeg", "jpg", "png", "webp"}:
                    return PhotoValidationResult(False, "unsupported_image_format", digest, width, height, image_format, mode)
        except (UnidentifiedImageError, OSError, ValueError):
            return PhotoValidationResult(False, "invalid_image", digest, 0, 0, "unknown", "unknown")

        image_bgr = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image_bgr is None:
            return PhotoValidationResult(False, "invalid_image", digest, 0, 0, "unknown", "unknown")

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        face_boxes = self._face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        has_face = len(face_boxes) > 0
        if photo_type == "skin_tone" and not has_face:
            return PhotoValidationResult(False, "face_not_detected", digest, width, height, image_format, mode, has_person=None, has_face=False)

        if photo_type == "tryon_reference":
            estimate = self.pose_estimator.estimate(image_bgr)
            quality = score_capture(estimate, photo_type=photo_type, threshold=self.quality_threshold)
            if not quality.ready_for_tryon:
                reason = quality.reasons[0] if quality.reasons else "capture_quality_below_threshold"
                return PhotoValidationResult(False, reason, digest, width, height, image_format, mode, has_person=estimate.detected, has_face=has_face, capture_quality=quality, pose_estimate=estimate)
            return PhotoValidationResult(True, None, digest, width, height, image_format, mode, has_person=estimate.detected, has_face=has_face, capture_quality=quality, pose_estimate=estimate)

        return PhotoValidationResult(True, None, digest, width, height, image_format, mode, has_person=None, has_face=has_face)
