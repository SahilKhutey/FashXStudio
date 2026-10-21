from uuid import uuid4

from database.models.identity import UserPhoto
from database.models.tryon import TryOnArtifact


def test_user_photo_null_quality_reasons_safe_access() -> None:
    photo = UserPhoto(
        id=uuid4(),
        user_id=uuid4(),
        photo_type="reference_photo",
        storage_key="test/key.jpg",
        status="accepted",
        quality_reasons=None,
    )
    assert photo.quality_reasons is None
    assert photo.safe_quality_reasons == []
    # Any mapper using `or []` pattern yields empty list:
    assert (photo.quality_reasons or []) == []


def test_user_photo_populated_quality_reasons() -> None:
    reasons = ["too_dark", "face_not_visible"]
    photo = UserPhoto(
        id=uuid4(),
        user_id=uuid4(),
        photo_type="reference_photo",
        storage_key="test/key.jpg",
        status="rejected",
        quality_reasons=reasons,
    )
    assert photo.quality_reasons == ["too_dark", "face_not_visible"]
    assert photo.safe_quality_reasons == ["too_dark", "face_not_visible"]
    assert (photo.quality_reasons or []) == ["too_dark", "face_not_visible"]


def test_tryon_artifact_null_quality_reasons_safe_access() -> None:
    artifact = TryOnArtifact(
        id=uuid4(),
        job_id=uuid4(),
        artifact_key="test-artifact-key",
        result_key="results/test.jpg",
        model_version="v1.0",
        pipeline_version="v1.0",
        photo_version=1,
        garment_version=1,
        quality_reasons=None,
    )
    assert artifact.quality_reasons is None
    assert artifact.safe_quality_reasons == []
    # Any mapper using `or []` pattern yields empty list:
    assert (artifact.quality_reasons or []) == []


def test_tryon_artifact_populated_quality_reasons() -> None:
    reasons = ["artifacts_present", "blur"]
    artifact = TryOnArtifact(
        id=uuid4(),
        job_id=uuid4(),
        artifact_key="test-artifact-key",
        result_key="results/test.jpg",
        model_version="v1.0",
        pipeline_version="v1.0",
        photo_version=1,
        garment_version=1,
        quality_reasons=reasons,
    )
    assert artifact.quality_reasons == ["artifacts_present", "blur"]
    assert artifact.safe_quality_reasons == ["artifacts_present", "blur"]
    assert (artifact.quality_reasons or []) == ["artifacts_present", "blur"]
