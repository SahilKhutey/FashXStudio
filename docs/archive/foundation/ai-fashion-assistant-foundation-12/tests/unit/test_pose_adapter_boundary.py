import pytest

from workers.profile_photo.pose.mediapipe_adapter import MediaPipePoseEstimator, PoseProviderUnavailable


def test_mediapipe_adapter_requires_model_path():
    with pytest.raises(PoseProviderUnavailable):
        MediaPipePoseEstimator(model_path="")
