import pytest

from scripts.rc11.evaluate_pilot import (
    evaluate_pilot_snapshot,
    percentile,
    ratio,
    validate_snapshot,
)


def sample_valid_snapshot():
    return {
        "metadata": {
            "pilot_id": "fashx-closed-beta-01",
            "period_start": "2026-11-16T00:00:00Z",
            "period_end": "2026-12-07T23:59:59Z",
            "extracted_at": "2026-12-08T08:00:00Z",
            "evidence_type": "real",
            "source_reference": "restricted://pilot/export/2026-12-08",
            "app_versions": ["0.9.0"],
            "ranker_versions": ["ranker-1"],
        },
        "counts": {
            "invited": 60,
            "login_invitees": 50,
            "onboarding_starters": 45,
            "activated_users": 32,
            "onboarding_completed": 38,
            "consent_starters": 45,
            "consent_abandoned": 3,
            "eligible_week2_users": 20,
            "week2_returned_users": 11,
            "tryon_submitted": 100,
            "tryon_completed": 92,
            "crash_free_sessions": 992,
            "total_sessions": 1000,
            "feed_cards_viewed": 500,
            "negative_feed_signals": 50,
            "week1_tryon_users": 25,
            "buy_click_users": 14,
            "verified_purchases": 4,
            "privacy_incidents": 0,
        },
        "ratings": {
            "tryon_realism": [4, 4, 5, 4, 4],
            "feed_relevance": [4, 3, 5, 4],
            "comfort_uploading_photo": [4, 5, 4, 4],
            "sus": [70, 72, 68],
            "pmf_very_disappointed": 4,
            "pmf_respondents": 10,
            "nps_promoters": 6,
            "nps_passives": 2,
            "nps_detractors": 2,
        },
        "tryon": {
            "latency_ms": [12000, 15000, 18000],
            "defect_flags": 0,
            "rated_outputs": 5,
            "tryons_per_activated_user": [3, 4, 4, 3],
            "minutes_to_first_tryon": [8, 9, 7, 6],
        },
        "safety": {
            "offensive_output_incidents": 0,
            "data_exposure_incidents": 0,
            "unresolved_stop_rules": 0,
            "vendor_spend_usd": 120,
            "vendor_budget_usd": 350,
        },
    }


def test_ratio_returns_none_for_zero_denominator():
    assert ratio(1, 0) is None
    assert ratio(1, -5) is None


def test_ratio_calculates_fraction():
    assert ratio(3, 4) == 0.75


def test_percentile_uses_nearest_rank():
    assert percentile([10, 20, 30, 40], 0.95) == 40
    assert percentile([10, 20, 30, 40], 0.50) == 20


def test_percentile_empty_is_unknown():
    assert percentile([], 0.95) is None


def test_percentile_rejects_invalid_percentile():
    with pytest.raises(ValueError):
        percentile([1, 2], 0)
    with pytest.raises(ValueError):
        percentile([1, 2], 1.5)


def test_missing_snapshot_fields_are_reported():
    missing = validate_snapshot({})
    assert "metadata.pilot_id" in missing
    assert "counts.invited" in missing
    assert "ratings.tryon_realism" in missing


def test_non_real_evidence_is_rejected_as_incomplete():
    snapshot = sample_valid_snapshot()
    snapshot["metadata"]["evidence_type"] = "simulated"
    result = evaluate_pilot_snapshot(snapshot)
    assert result.decision == "INCOMPLETE_EVIDENCE"
    assert "evidence_type_not_real" in result.stop_reasons


def test_full_fixture_evaluation_passes_go_review():
    snapshot = sample_valid_snapshot()
    evaluation = evaluate_pilot_snapshot(snapshot)
    assert evaluation.decision == "GO_REVIEW_REQUIRED"
    assert len(evaluation.must_haves) == 5
    assert all(m.passed for m in evaluation.must_haves)
    assert len(evaluation.should_haves) == 4
    assert all(s.passed for s in evaluation.should_haves)
    assert not evaluation.stop_reasons


def test_stop_rule_data_exposure_triggers_hold():
    snapshot = sample_valid_snapshot()
    snapshot["safety"]["data_exposure_incidents"] = 1
    evaluation = evaluate_pilot_snapshot(snapshot)
    assert evaluation.decision == "HOLD_SAFETY_TRIGGERED"
    assert "suspected_data_exposure" in evaluation.stop_reasons


def test_stop_rule_crash_spike_triggers_hold():
    snapshot = sample_valid_snapshot()
    snapshot["counts"]["crash_free_sessions"] = 950  # 95% < 98%
    evaluation = evaluate_pilot_snapshot(snapshot)
    assert evaluation.decision == "HOLD_SAFETY_TRIGGERED"
    assert "stability_crash_spike" in evaluation.stop_reasons
