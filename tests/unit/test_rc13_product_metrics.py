from scripts.rc13.evaluate_product_metrics import (
    ProductDecision,
    evaluate_product_metrics,
)


def sample_metrics() -> dict[str, object]:
    return {
        "M1_login_invitee_completion_rate": 0.65,
        "M1_onboarding_starter_completion_rate": 0.84,
        "M2_mean_vto_rating": 4.10,
        "M2_ratings_gte_4_rate": 0.78,
        "M2_defect_rate": 0.08,
        "M3_crash_free_sessions": 0.995,
        "M3_tryon_success_rate": 0.94,
        "M3_p95_latency_seconds": 28.5,
        "M4_privacy_incident_count": 0,
        "M4_photo_comfort_agreement_rate": 0.86,
        "M4_consent_dropoff_rate": 0.06,
        "M5_week2_return_rate": 0.54,
        "S1_feed_relevance_rating_gte_4_rate": 0.68,
        "S1_negative_feed_signal_rate": 0.11,
        "S2_week1_tryon_rate": 0.72,
        "S2_median_tryons_per_user": 4.0,
        "S2_median_minutes_to_first_tryon": 6.5,
        "S3_buy_click_rate": 0.44,
        "S3_verified_purchases": 5,
        "S4_sus_score": 74.0,
        "S4_pmf_very_disappointed_rate": 0.36,
        "S4_nps_score": 28.0,
        "is_synthetic": False,
    }


def test_all_frozen_metrics_pass_returns_go():
    res = evaluate_product_metrics(sample_metrics())
    assert res.decision == ProductDecision.GO
    assert len(res.passed_must_haves) == 12
    assert not res.failed_must_haves
    assert not res.unknown_must_haves
    assert len(res.passed_should_groups) == 4


def test_must_have_below_threshold_fails():
    metrics = sample_metrics()
    metrics["M1_login_invitee_completion_rate"] = 0.55  # Below 0.60 target
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.FIX_AND_RERUN
    assert "M1_login_invitee_completion_rate" in res.failed_must_haves


def test_privacy_and_realism_failures_trigger_pivot_or_stop():
    metrics = sample_metrics()
    metrics["M2_mean_vto_rating"] = 2.5  # Critical realism failure
    metrics["M4_photo_comfort_agreement_rate"] = 0.40  # Critical trust failure
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.PIVOT_OR_STOP


def test_missing_must_have_metric_holds():
    metrics = sample_metrics()
    del metrics["M3_crash_free_sessions"]
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.HOLD
    assert "M3_crash_free_sessions" in res.unknown_must_haves


def test_stop_rule_triggered_holds():
    metrics = sample_metrics()
    metrics["stop_suspected_data_exposure"] = True
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.HOLD
    assert "stop_suspected_data_exposure" in res.triggered_stop_rules


def test_synthetic_metrics_rejected_by_default():
    metrics = sample_metrics()
    metrics["is_synthetic"] = True
    res = evaluate_product_metrics(metrics, allow_synthetic=False)
    assert res.decision == ProductDecision.HOLD
    assert "synthetic_metrics_rejected_for_release_governance" in res.reasons


def test_fewer_than_3_should_have_groups_requires_fix():
    metrics = sample_metrics()
    # Remove S1, S2, S3
    for k in list(metrics.keys()):
        if k.startswith(("S1_", "S2_", "S3_")):
            del metrics[k]
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.FIX_AND_RERUN
    assert any("insufficient_should_have_groups" in r for r in res.reasons)
