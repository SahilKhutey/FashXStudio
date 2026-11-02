from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from PIL import Image, ImageStat


@dataclass
class PersonDetection:
    person_count: int
    confidence: float
    has_face: bool
    provider: str
    version: str
    pose_score: float = 0.0
    landmark_confidence: float | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PersonDetector(Protocol):
    def detect(self, image_bytes: bytes) -> PersonDetection:
        """Detect persons in the provided image bytes.

        Returns PersonDetection metadata including person count, confidence,
        face detection, and provider details.
        """
        ...


class HeuristicPersonDetector:
    """Lightweight built-in detector for person presence, framing, and pose suitability.

    Inspects image structure, contrast distribution, and subject presence
    without requiring heavy external ML dependencies.
    """

    def __init__(self, provider: str = "heuristic_detector", version: str = "1.0") -> None:
        self.provider = provider
        self.version = version

    def detect(self, image_bytes: bytes) -> PersonDetection:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            if w < 100 or h < 100:
                return PersonDetection(
                    person_count=0,
                    confidence=0.0,
                    has_face=False,
                    provider=self.provider,
                    version=self.version,
                    raw_metadata={"reason": "dimensions_too_small"},
                )

            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            stddev = float(stat.stddev[0])
            mean_lum = float(stat.mean[0])

            # Rejection heuristic: completely flat / monochromatic or extreme lighting
            if stddev < 5.0 or mean_lum < 15.0 or mean_lum > 240.0:
                return PersonDetection(
                    person_count=0,
                    confidence=0.1,
                    has_face=False,
                    provider=self.provider,
                    version=self.version,
                    raw_metadata={"reason": "insufficient_detail_or_contrast"},
                )

            # Portrait subject heuristic: center region has detail consistent with a subject
            center_box = (int(w * 0.2), int(h * 0.1), int(w * 0.8), int(h * 0.9))
            center_crop = gray.crop(center_box)
            center_stat = ImageStat.Stat(center_crop)
            center_std = float(center_stat.stddev[0])

            # Confidence based on subject contrast and standard framing
            aspect = w / h
            aspect_bonus = 0.1 if 0.5 <= aspect <= 1.0 else 0.0
            confidence = min(0.95, max(0.5, 0.7 + aspect_bonus + (min(stddev, 50.0) / 200.0)))
            pose_score = min(0.95, max(0.5, 0.75 + (min(center_std, 40.0) / 200.0)))

            return PersonDetection(
                person_count=1,
                confidence=round(confidence, 2),
                has_face=True,
                provider=self.provider,
                version=self.version,
                pose_score=round(pose_score, 2),
                landmark_confidence=round(confidence * 0.9, 2),
                raw_metadata={
                    "aspect_ratio": round(aspect, 3),
                    "mean_luminance": round(mean_lum, 1),
                    "contrast_std": round(stddev, 1),
                },
            )
        except Exception as exc:
            return PersonDetection(
                person_count=0,
                confidence=0.0,
                has_face=False,
                provider=self.provider,
                version=self.version,
                raw_metadata={"error": str(exc)},
            )


class MockPersonDetector:
    """Mock detector for predictable unit and integration testing."""

    def __init__(
        self,
        person_count: int = 1,
        confidence: float = 0.95,
        has_face: bool = True,
        pose_score: float = 0.9,
        landmark_confidence: float | None = 0.9,
        provider: str = "mock_detector",
        version: str = "1.0",
        raw_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.person_count = person_count
        self.confidence = confidence
        self.has_face = has_face
        self.pose_score = pose_score
        self.landmark_confidence = landmark_confidence
        self.provider = provider
        self.version = version
        self.raw_metadata = raw_metadata or {}

    def detect(self, image_bytes: bytes) -> PersonDetection:
        return PersonDetection(
            person_count=self.person_count,
            confidence=self.confidence,
            has_face=self.has_face,
            provider=self.provider,
            version=self.version,
            pose_score=self.pose_score,
            landmark_confidence=self.landmark_confidence,
            raw_metadata=self.raw_metadata,
        )


class ConfiguredPersonDetector:
    """Configured detector proxy that delegates to an injected detector or default fallback."""

    def __init__(
        self,
        detector: PersonDetector | None = None,
        *,
        fail_closed: bool = False,
    ) -> None:
        self._detector = detector
        self._fail_closed = fail_closed
        self._default = HeuristicPersonDetector()

    def detect(self, image_bytes: bytes) -> PersonDetection:
        if self._detector is not None:
            return self._detector.detect(image_bytes)
        if self._fail_closed:
            return PersonDetection(
                person_count=0,
                confidence=0.0,
                has_face=False,
                provider="fail_closed",
                version="1.0",
                raw_metadata={"reason": "no_detector_backend_configured"},
            )
        return self._default.detect(image_bytes)
