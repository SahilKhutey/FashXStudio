from __future__ import annotations

from fashx.catalog.enrichment.confidence import decide_review
from fashx.catalog.enrichment.contracts import ReviewFlag, ReviewStatus


def test_enr_021_high_confidence_supported_attribute_auto_accepted() -> None:
    """Verify ENR-021: Attributes with >= 0.95 confidence and evidence are auto-accepted."""
    decision = decide_review("color", 0.98, evidence_present=True)
    assert decision.review_required is False
    assert decision.review_status == ReviewStatus.AUTO_ACCEPTED
    assert len(decision.flags) == 0


def test_enr_020_low_confidence_occasion_requires_review() -> None:
    """Verify ENR-020: Sensitive or subjective attributes (occasion) with < 0.95 require review."""
    decision = decide_review("occasion", 0.75, evidence_present=True)
    assert decision.review_required is True
    assert decision.review_status == ReviewStatus.PENDING_REVIEW
    assert ReviewFlag.LOW_CONFIDENCE in decision.flags


def test_conflicting_evidence_triggers_review() -> None:
    """Verify that conflicting evidence immediately triggers human review flag."""
    decision = decide_review("color", 0.99, evidence_present=True, conflicting=True)
    assert decision.review_required is True
    assert decision.review_status == ReviewStatus.PENDING_REVIEW
    assert ReviewFlag.CONFLICTING_EVIDENCE in decision.flags


def test_missing_evidence_triggers_review() -> None:
    """Verify that missing evidence triggers human review."""
    decision = decide_review("color", 0.99, evidence_present=False)
    assert decision.review_required is True
    assert decision.review_status == ReviewStatus.PENDING_REVIEW
    assert ReviewFlag.MISSING_EVIDENCE in decision.flags
