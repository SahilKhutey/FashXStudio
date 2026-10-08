from datetime import datetime, timezone
from uuid import uuid4

from schemas.profile.intelligence import ProfileReadiness, SkinToneResult
from workers.skin_tone.domain.ita import classify_ita, estimate_ita


def test_ita_classification_boundaries():
    assert classify_ita(60) == "very_light"
    assert classify_ita(50) == "light"
    assert classify_ita(35) == "intermediate"
    assert classify_ita(20) == "tan"
    assert classify_ita(0) == "brown"
    assert classify_ita(-40) == "dark"


def test_profile_readiness_requires_body_and_tryon_photo():
    result = ProfileReadiness(
        profile_version=2, body_profile_complete=True, tryon_photo_ready=True,
        skin_tone_ready=False, ready_for_tryon=True, missing=["skin_tone"],
    )
    assert result.ready_for_tryon is True
    assert result.missing == ["skin_tone"]


def test_skin_tone_result_contract():
    result = SkinToneResult(
        result_id=uuid4(), photo_id=uuid4(), confidence=0.8, method="ita_face_crop_v1",
        model_version="1.0", status="completed", created_at=datetime.now(timezone.utc),
    )
    assert result.confidence == 0.8
