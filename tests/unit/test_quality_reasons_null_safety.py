from uuid import uuid4

from database.models.identity import UserPhoto
from database.models.tryon import TryOnArtifact
from fashx.profile.router import UserPhotoItem
from fashx.tryon.router import TryOnArtifactResponse


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


def test_user_photo_null_quality_reasons_serializes_via_response_model() -> None:
    photo = UserPhoto(
        id=uuid4(),
        user_id=uuid4(),
        photo_type="reference_photo",
        storage_key="test/key.jpg",
        status="accepted",
        reject_reason=None,
        quality_reasons=None,
    )
    # Real API response model mapping
    item = UserPhotoItem(
        id=photo.id,
        photo_type=photo.photo_type,
        status=photo.status,
        storage_key=photo.storage_key,
        reject_reason=photo.reject_reason,
        quality_reasons=photo.quality_reasons or [],
    )
    assert item.quality_reasons == []
    dumped = item.model_dump()
    assert dumped["quality_reasons"] == []


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
    item = UserPhotoItem(
        id=photo.id,
        photo_type=photo.photo_type,
        status=photo.status,
        storage_key=photo.storage_key,
        reject_reason=photo.reject_reason,
        quality_reasons=photo.quality_reasons or [],
    )
    assert item.quality_reasons == ["too_dark", "face_not_visible"]
    assert item.model_dump()["quality_reasons"] == ["too_dark", "face_not_visible"]


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
    assert (artifact.quality_reasons or []) == []


def test_tryon_artifact_null_quality_reasons_serializes_via_response_model() -> None:
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
    resp = TryOnArtifactResponse(
        artifact_key=artifact.artifact_key,
        result_key=artifact.result_key,
        model_version=artifact.model_version,
        pipeline_version=artifact.pipeline_version,
        photo_version=artifact.photo_version,
        garment_version=artifact.garment_version,
        quality_reasons=artifact.quality_reasons or [],
    )
    assert resp.quality_reasons == []
    dumped = resp.model_dump()
    assert dumped["quality_reasons"] == []


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
    resp = TryOnArtifactResponse(
        artifact_key=artifact.artifact_key,
        result_key=artifact.result_key,
        model_version=artifact.model_version,
        pipeline_version=artifact.pipeline_version,
        photo_version=artifact.photo_version,
        garment_version=artifact.garment_version,
        quality_reasons=artifact.quality_reasons or [],
    )
    assert resp.quality_reasons == ["artifacts_present", "blur"]
    assert resp.model_dump()["quality_reasons"] == ["artifacts_present", "blur"]
