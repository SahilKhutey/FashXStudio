from api.app.core.readiness_audit import ProductionReadinessAuditor


def test_g2_ml_quality_gate() -> None:
    # Pass case
    pass_res = ProductionReadinessAuditor.audit_g2_ml_quality(
        attribute_completeness=0.985,
        silhouette_accuracy=0.94,
        color_accuracy=0.96,
    )
    assert pass_res.passed is True
    assert pass_res.gate_id == "G2"

    # Fail case
    fail_res = ProductionReadinessAuditor.audit_g2_ml_quality(
        attribute_completeness=0.91,  # Below 0.95
        silhouette_accuracy=0.94,
        color_accuracy=0.96,
    )
    assert fail_res.passed is False


def test_g3_performance_gate() -> None:
    pass_res = ProductionReadinessAuditor.audit_g3_performance(
        api_p95_ms=95.0,
        feed_latency_ms=180.0,
        tryon_latency_sec=4.2,
    )
    assert pass_res.passed is True

    fail_res = ProductionReadinessAuditor.audit_g3_performance(
        api_p95_ms=190.0,  # Exceeds 150ms
        feed_latency_ms=180.0,
        tryon_latency_sec=4.2,
    )
    assert fail_res.passed is False


def test_g4_privacy_gate() -> None:
    pass_res = ProductionReadinessAuditor.audit_g4_privacy(
        photos_purged=3,
        storage_objects_purged=3,
        residual_leaked_count=0,
    )
    assert pass_res.passed is True

    fail_res = ProductionReadinessAuditor.audit_g4_privacy(
        photos_purged=3,
        storage_objects_purged=2,  # Storage mismatch
        residual_leaked_count=1,
    )
    assert fail_res.passed is False


def test_g5_commercial_authorization_gate() -> None:
    # In production, research-only model fails Gate G5 (Rule I08)
    prod_fail = ProductionReadinessAuditor.audit_g5_commercial_clearance(
        environment="production",
        is_model_commercial_cleared=False,
        has_affiliate_attribution=True,
    )
    assert prod_fail.passed is False

    # In production, commercial model passes Gate G5
    prod_pass = ProductionReadinessAuditor.audit_g5_commercial_clearance(
        environment="production",
        is_model_commercial_cleared=True,
        has_affiliate_attribution=True,
    )
    assert prod_pass.passed is True

    # In test environment, evaluation model is permitted
    test_eval = ProductionReadinessAuditor.audit_g5_commercial_clearance(
        environment="test",
        is_model_commercial_cleared=False,
        has_affiliate_attribution=True,
    )
    assert test_eval.passed is True


def test_g6_user_acceptance_gate() -> None:
    pass_res = ProductionReadinessAuditor.audit_g6_user_acceptance(
        tryon_realism_satisfaction_pct=82.0,
        feed_relevance_satisfaction_pct=88.5,
    )
    assert pass_res.passed is True

    fail_res = ProductionReadinessAuditor.audit_g6_user_acceptance(
        tryon_realism_satisfaction_pct=70.0,  # Below 75%
        feed_relevance_satisfaction_pct=88.5,
    )
    assert fail_res.passed is False
