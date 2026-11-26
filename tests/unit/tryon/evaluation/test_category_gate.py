"""Unit tests for category acceptance gates and policy enforcement (Phase 07.7).

Covers GATE-001 through GATE-012.
"""

from __future__ import annotations

from fashx.tryon.evaluation.category_gate import (
    CategoryMetrics,
    evaluate_category,
    get_category_rejection_message,
)
from fashx.tryon.evaluation.contracts import (
    CategoryStatus,
    is_vto_category_allowed,
)


def passing_metrics(category: str = "tshirts") -> CategoryMetrics:
    return CategoryMetrics(
        category=category,
        sample_count=40,
        job_success_rate=0.95,
        garment_preservation=4.1,
        body_alignment=4.0,
        artifact_quality=4.0,
        identity_preservation=4.2,
        visual_plausibility=4.0,
        non_misleading=4.5,
        reviewer_rejection_rate=0.02,
        critical_misleading_count=0,
    )


def test_category_passes_all_gates():
    """GATE-001: Category passing all thresholds receives APPROVED_LIMITED."""
    res = evaluate_category(passing_metrics())
    assert res.passed is True
    assert res.status == CategoryStatus.APPROVED_LIMITED
    assert res.failures == []


def test_category_fails_low_garment_preservation():
    """GATE-002: Garment preservation below 3.8 fails gate."""
    metrics = CategoryMetrics(
        category="tshirts",
        sample_count=40,
        job_success_rate=0.95,
        garment_preservation=3.5,  # < 3.8
        body_alignment=4.0,
        artifact_quality=4.0,
        identity_preservation=4.2,
        visual_plausibility=4.0,
        non_misleading=4.5,
        reviewer_rejection_rate=0.02,
        critical_misleading_count=0,
    )
    res = evaluate_category(metrics)
    assert res.passed is False
    assert res.status == CategoryStatus.NEEDS_IMPROVEMENT
    assert any("Garment preservation" in f for f in res.failures)


def test_category_fails_critical_misleading():
    """GATE-005: Any critical misleading output immediately BLOCKS the category."""
    metrics = CategoryMetrics(
        category="sarees",
        sample_count=40,
        job_success_rate=0.95,
        garment_preservation=4.2,
        body_alignment=4.1,
        artifact_quality=4.0,
        identity_preservation=4.2,
        visual_plausibility=4.0,
        non_misleading=4.5,
        reviewer_rejection_rate=0.02,
        critical_misleading_count=1,  # Critical issue detected
    )
    res = evaluate_category(metrics)
    assert res.passed is False
    assert res.status == CategoryStatus.BLOCKED
    assert any("Critical misleading outputs detected" in f for f in res.failures)


def test_insufficient_sample_count():
    """GATE-006: Sample count < 30 cannot pass; remains EVALUATING."""
    metrics = CategoryMetrics(
        category="dresses",
        sample_count=15,  # < 30
        job_success_rate=1.0,
        garment_preservation=4.5,
        body_alignment=4.5,
        artifact_quality=4.5,
        identity_preservation=4.5,
        visual_plausibility=4.5,
        non_misleading=4.5,
        reviewer_rejection_rate=0.0,
        critical_misleading_count=0,
    )
    res = evaluate_category(metrics)
    assert res.passed is False
    assert res.status == CategoryStatus.EVALUATING
    assert any("Insufficient sample count" in f for f in res.failures)


def test_is_vto_category_allowed_check():
    """GATE-008: is_vto_category_allowed returns True ONLY for APPROVED_LIMITED."""
    assert is_vto_category_allowed(CategoryStatus.APPROVED_LIMITED) is True
    assert is_vto_category_allowed(CategoryStatus.BLOCKED) is False
    assert is_vto_category_allowed(CategoryStatus.EVALUATING) is False
    assert is_vto_category_allowed(CategoryStatus.NEEDS_IMPROVEMENT) is False
    assert is_vto_category_allowed(CategoryStatus.NOT_EVALUATED) is False


def test_rejection_message_format():
    """GATE-009: Empathetic shopper rejection message is clear and non-technical."""
    msg = get_category_rejection_message("sarees")
    assert "not currently available" in msg
    assert "sarees" in msg
    assert "view the product details" in msg
