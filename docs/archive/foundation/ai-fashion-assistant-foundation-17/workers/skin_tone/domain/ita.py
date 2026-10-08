from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(frozen=True)
class ITAResult:
    ita_degrees: float | None
    tone_class: str | None
    confidence: float
    method: str
    model_version: str


def classify_ita(ita: float) -> str:
    if ita > 55:
        return "very_light"
    if ita > 41:
        return "light"
    if ita > 28:
        return "intermediate"
    if ita > 10:
        return "tan"
    if ita > -30:
        return "brown"
    return "dark"


def estimate_ita(image_bgr: np.ndarray) -> ITAResult:
    if image_bgr is None or image_bgr.size == 0:
        return ITAResult(None, None, 0.0, "ita_face_crop_v1", "1.0")

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face_model = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(face_model)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64))
    if len(faces) == 0:
        return ITAResult(None, None, 0.0, "ita_face_crop_v1", "1.0")

    x, y, w, h = max(faces, key=lambda f: int(f[2]) * int(f[3]))
    crop = image_bgr[y + int(h * 0.20): y + int(h * 0.88), x + int(w * 0.16): x + int(w * 0.84)]
    if crop.size == 0:
        return ITAResult(None, None, 0.0, "ita_face_crop_v1", "1.0")

    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32)
    lstar = lab[..., 0] * (100.0 / 255.0)
    astar = lab[..., 1] - 128.0
    bstar = lab[..., 2] - 128.0

    # Exclude very dark/bright pixels and approximate chroma outliers before aggregation.
    valid = (lstar > 20) & (lstar < 95) & (np.abs(astar) < 40) & (bstar > 0) & (bstar < 60)
    if int(valid.sum()) < 50:
        return ITAResult(None, None, 0.0, "ita_face_crop_v1", "1.0")

    mean_l = float(np.median(lstar[valid]))
    mean_a = float(np.median(astar[valid]))
    mean_b = float(np.median(bstar[valid]))
    if abs(mean_b - mean_a) < 1e-3:
        return ITAResult(None, None, 0.0, "ita_face_crop_v1", "1.0")

    ita = float(np.degrees(np.arctan2(mean_l - 50.0, mean_b - mean_a)))
    ratio = min(1.0, float(valid.sum()) / float(valid.size))
    confidence = max(0.0, min(1.0, 0.45 + 0.55 * ratio))
    return ITAResult(ita, classify_ita(ita), confidence, "ita_face_crop_v1", "1.0")
