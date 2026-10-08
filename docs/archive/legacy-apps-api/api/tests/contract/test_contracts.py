"""
Contract Tests: Pydantic v2 Domain Contracts (/schemas)
Verifies schema invariants, immutability, extra-field rejection, and provenance tracking.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from schemas.feedback.v1 import FitFeedbackV1, FitOutcome, Disposition, PreferenceAction, PreferenceFeedbackV1
from schemas.profile.v1 import MeasurementSource, MeasurementType, MeasurementV1, UserConsentV1


def test_measurement_provenance_and_confidence():
    """Rule I11: Measurements must record origin source and confidence score."""
    m = MeasurementV1(
        measurement_id="m_101",
        user_id="usr_1",
        measurement_type=MeasurementType.CHEST,
        value=101.5,
        unit="cm",
        source=MeasurementSource.COMPUTER_VISION_ESTIMATED,
        confidence=0.88,
        captured_at=datetime.now(timezone.utc),
        profile_version=1,
    )
    assert m.source == "computer_vision_estimated"
    assert m.confidence == 0.88
    assert m.schema_version == "1.0"


def test_schema_rejects_extra_fields():
    """All domain contracts must reject unknown extra fields (extra='forbid')."""
    with pytest.raises(ValidationError):
        MeasurementV1(
            measurement_id="m_101",
            user_id="usr_1",
            measurement_type=MeasurementType.CHEST,
            value=101.5,
            source=MeasurementSource.USER_REPORTED,
            captured_at=datetime.now(timezone.utc),
            profile_version=1,
            malicious_extra_field="should_be_rejected",  # Extra field
        )


def test_fit_feedback_granularity():
    """Rule I11: Fit feedback must record brand + category + fit_type + size."""
    fb = FitFeedbackV1(
        feedback_id="fb_001",
        user_id="usr_1",
        brand="Selected Homme",
        category="shirt",
        fit_type="relaxed",
        canonical_garment_id="cg_1",
        variant_id="gv_1",
        purchased_size="M",
        overall_fit=FitOutcome.SLIGHTLY_TIGHT,
        disposition=Disposition.KEPT,
        timestamp=datetime.now(timezone.utc),
    )
    assert fb.overall_fit == "slightly_tight"
    assert fb.brand == "Selected Homme"
    assert fb.category == "shirt"


def test_consent_defaults_to_false_for_training():
    """Rule I12: ml_model_training consent must strictly default to False."""
    consent = UserConsentV1(
        user_id="usr_1",
        body_photo_processing={"granted": True},
        measurement_extraction={"granted": True},
        camera_stream_access={"granted": False},
        personalization_profiling={"granted": True},
        updated_at=datetime.now(timezone.utc),
    )
    assert consent.ml_model_training.granted is False
    assert consent.body_photo_processing.granted is True
