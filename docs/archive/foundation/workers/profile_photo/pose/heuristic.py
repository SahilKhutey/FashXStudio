from __future__ import annotations

import cv2

from .types import PoseEstimate


class HeuristicPoseEstimator:
    """Low-cost fallback for environments without a pose landmark runtime.

    It is deliberately conservative: it estimates capture geometry from the
    detected face/person region but never claims landmark-level pose accuracy.
    """

    provider = "opencv_heuristic"
    provider_version = cv2.__version__

    def __init__(self, face_detector=None):
        self._face = face_detector or cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def estimate(self, image_bgr) -> PoseEstimate:
        height, width = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        rects, weights = self._hog.detectMultiScale(
            image_bgr, winStride=(8, 8), padding=(16, 16), scale=1.05
        )
        detected = bool(len(rects) > 0 or len(faces) > 0)
        if not detected:
            return PoseEstimate(self.provider, self.provider_version, False, 0, 0.0)

        if len(rects) > 0:
            x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
            conf = float(max(weights)) if len(weights) else 0.0
            centered = 1.0 - min(1.0, abs((x + w / 2) / width - 0.5) * 2.0)
            return PoseEstimate(
                self.provider, self.provider_version, True, 0, max(0.0, min(1.0, conf)),
                body_height_ratio=h / height,
                centeredness=centered,
            )
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        centered = 1.0 - min(1.0, abs((x + w / 2) / width - 0.5) * 2.0)
        return PoseEstimate(
            self.provider, self.provider_version, True, 0, 0.5,
            body_height_ratio=h / height,
            centeredness=centered,
        )
