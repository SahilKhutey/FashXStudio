from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PoseLandmark:
    name: str
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.0


@dataclass(frozen=True)
class PoseEstimate:
    provider: str
    provider_version: str
    detected: bool
    landmark_count: int
    mean_visibility: float
    landmarks: tuple[PoseLandmark, ...] = field(default_factory=tuple)
    shoulder_width_ratio: float | None = None
    body_height_ratio: float | None = None
    centeredness: float | None = None


class PoseEstimator:
    def estimate(self, image_bgr) -> PoseEstimate:  # pragma: no cover - protocol-like base
        raise NotImplementedError
