from scripts.rc13.evaluate_product_metrics import (
    ProductDecision,
    evaluate_product_metrics,
)


def sample_metrics() -> dict[str, object]:
    return {
        "activation_login_rate": 0.75,
        "tryon_completion_rate": 0.68,
        "vto_mean_rating": 4.1,
        "crash_free_sessions": 0.995,
        "privacy_incident_count": 0,
        "week2_retention_rate": 0.24,
        "retailer_clickout_rate": 0.18,
        "is_synthetic": False,
    }


def test_all_metrics_pass_threshold():
    res = evaluate_product_metrics(sample_metrics())
    assert res.decision == ProductDecision.PASS
    assert len(res.passed) == 5
    assert not res.failed
    assert not res.unknown


def test_metric_below_threshold_fails():
    metrics = sample_metrics()
    metrics["activation_login_rate"] = 0.65  # Below 0.70 target
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.FAIL
    assert "activation_login_rate" in res.failed
    assert any("activation_login_rate_below_threshold" in r for r in res.reasons)


def test_privacy_incident_fails():
    metrics = sample_metrics()
    metrics["privacy_incident_count"] = 1  # Target is <= 0
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.FAIL
    assert "privacy_incident_count" in res.failed


def test_missing_metric_holds():
    metrics = sample_metrics()
    del metrics["crash_free_sessions"]
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.HOLD
    assert "crash_free_sessions" in res.unknown
    assert any("metric_crash_free_sessions_missing" in r for r in res.reasons)


def test_invalid_metric_value_holds():
    metrics = sample_metrics()
    metrics["vto_mean_rating"] = "invalid_numeric"
    res = evaluate_product_metrics(metrics)
    assert res.decision == ProductDecision.HOLD
    assert "vto_mean_rating" in res.unknown


def test_synthetic_metrics_rejected_by_default():
    metrics = sample_metrics()
    metrics["is_synthetic"] = True
    res = evaluate_product_metrics(metrics, allow_synthetic=False)
    assert res.decision == ProductDecision.HOLD
    assert "synthetic_metrics_rejected" in res.reasons

    # Allowed when explicitly specified
    res_allowed = evaluate_product_metrics(metrics, allow_synthetic=True)
    assert res_allowed.decision == ProductDecision.PASS


def test_optional_metrics_evaluated():
    metrics = sample_metrics()
    res = evaluate_product_metrics(metrics)
    assert "week2_retention_rate" in res.metrics
    assert res.metrics["week2_retention_rate"].status == "pass"
