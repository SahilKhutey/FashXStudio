"""Tests for Visual Try-On Presentation Policy and Disclaimers (DISC-001..010)."""

from fashx.presentation.claims import (
    CLAIM_COPY,
    ClaimType,
    enforce_merchant_widget_policy,
    get_presentation_policy,
)


def test_disc_001_vto_result_type():
    policy = get_presentation_policy()
    assert policy["presentation"]["result_type"] == "VISUAL_TRY_ON"


def test_disc_002_disclaimer_code_present():
    policy = get_presentation_policy()
    assert policy["presentation"]["disclaimer_code"] == "VISUAL_TRYON_NOT_FIT_VERIFICATION"


def test_disc_003_saved_result_disclaimer():
    copy = CLAIM_COPY[ClaimType.VISUAL_SIMULATION]
    assert "visual" in copy["title"].lower()
    assert "does not verify" in copy["description"].lower()


def test_disc_004_shareable_result_presentation():
    policy = get_presentation_policy()
    pres = policy["presentation"]
    assert pres["is_ai_generated"] is True
    assert pres["fit_verified"] is False
    assert pres["fit_guaranteed"] is False


def test_disc_005_caption_and_action():
    copy = CLAIM_COPY[ClaimType.VISUAL_SIMULATION]
    assert copy["caption"] == "AI-generated visual simulation"
    assert copy["action"] == "View merchant size chart"


def test_disc_006_missing_fit_recommendation():
    policy = get_presentation_policy(fit_recommendation_available=False)
    assert policy["presentation"]["fit_recommendation_available"] is False


def test_disc_007_fit_verified_always_false():
    # Attempting to request verified fit still produces fit_verified = False
    policy = get_presentation_policy(result_type="VERIFIED_FIT")
    assert policy["presentation"]["fit_verified"] is False
    assert policy["presentation"]["result_type"] == "VISUAL_TRY_ON"


def test_disc_008_client_override_prevention():
    policy = get_presentation_policy()
    assert policy["presentation"]["fit_guaranteed"] is False
    assert policy["presentation"]["fit_prediction_id"] is None


def test_disc_009_merchant_widget_disclaimer_locked():
    hacked_config = {
        "show_disclaimer": False,
        "disclaimer_text": "",
        "allow_fit_guarantee": True,
    }
    sanitized = enforce_merchant_widget_policy(hacked_config)
    assert sanitized["show_disclaimer"] is True
    assert sanitized["disclaimer_locked"] is True
    assert sanitized["allow_fit_guarantee"] is False
    assert "does not verify" in sanitized["disclaimer_text"].lower()


def test_disc_010_fallback_presentation():
    policy = get_presentation_policy("UNKNOWN_TYPE")
    assert policy["presentation"]["result_type"] == "VISUAL_TRY_ON"
    assert policy["presentation"]["policy_version"] == "presentation-v1"
