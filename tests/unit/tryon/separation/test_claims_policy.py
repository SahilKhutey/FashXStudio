"""Tests for Claims and Content Policy (COPY-001..010)."""

import pytest

from fashx.presentation.claims import (
    assert_claim_valid,
    enforce_merchant_widget_policy,
    validate_claim_text,
)


def test_copy_001_approved_wording_allowed():
    assert validate_claim_text("See how this garment might look on you") is True
    assert validate_claim_text("Preview how this garment looks in virtual try-on") is True


def test_copy_002_guaranteed_fit_rejected():
    assert validate_claim_text("This dress has guaranteed fit for all sizes") is False
    assert validate_claim_text("Guaranteed-fit before checkout") is False


def test_copy_003_perfect_fit_rejected():
    assert validate_claim_text("Find your perfect fit with AI") is False
    assert validate_claim_text("Our AI delivers a perfect-fit every time") is False


def test_copy_004_verified_physical_fit_rejected():
    assert validate_claim_text("Verified physical fit calculated from your picture") is False
    assert validate_claim_text("Verified fit confirmed") is False


def test_copy_005_exact_body_fit_rejected():
    assert validate_claim_text("Your exact body fit shown in 3D") is False


def test_copy_006_this_size_will_fit_you_rejected():
    assert validate_claim_text("This size will fit you perfectly") is False


def test_copy_007_never_get_wrong_size_rejected():
    assert validate_claim_text("Never get the wrong size again with FashX") is False


def test_copy_008_ai_confirms_fits_rejected():
    assert validate_claim_text("AI confirms this garment fits your dimensions") is False


def test_copy_009_widget_policy_sanitizes_prohibited_label():
    bad_config = {
        "result_label": "Your Guaranteed Fit",
        "disclaimer_text": "AI confirmed perfect fit",
    }
    cleaned = enforce_merchant_widget_policy(bad_config)
    assert "guaranteed" not in cleaned["result_label"].lower()
    assert "AI-generated visual try-on" in cleaned["result_label"]
    assert "does not verify" in cleaned["disclaimer_text"].lower()


def test_copy_010_assert_claim_valid_raises_value_error():
    with pytest.raises(ValueError, match="unsupported guaranteed fit"):
        assert_claim_valid("Guaranteed fit for every shopper")
    # Valid claim raises nothing
    assert_claim_valid("AI-generated visual simulation")
