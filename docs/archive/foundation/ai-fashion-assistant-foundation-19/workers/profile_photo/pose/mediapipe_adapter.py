from __future__ import annotations

from .types import PoseEstimate


class PoseProviderUnavailable(RuntimeError):
    pass


class MediaPipePoseEstimator:
    """Adapter boundary for the production MediaPipe Pose Landmarker runtime.

    The model asset is deployment configuration, not source code. This adapter
    deliberately fails closed when the runtime/model asset is unavailable so a
    missing pose model can never silently downgrade a production capture gate.
    """

    provider = "mediapipe_pose_landmarker"

    def __init__(self, *, model_path: str):
        if not model_path:
            raise PoseProviderUnavailable("POSE_MODEL_PATH is required")
        try:
            import mediapipe  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise PoseProviderUnavailable("mediapipe is not installed") from exc
        self._mp = mediapipe
        self._model_path = model_path
        self.provider_version = getattr(mediapipe, "__version__", "unknown")

    def estimate(self, image_bgr) -> PoseEstimate:  # pragma: no cover - requires runtime model asset
        raise PoseProviderUnavailable(
            "MediaPipe Pose Landmarker runtime is configured but the deployment adapter/model asset is not installed in this environment"
        )
