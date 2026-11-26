"""Unit tests for human quality ratings, scoring rubric, and consensus (Phase 07.7).

Covers QUAL-001 through QUAL-010.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fashx.tryon.evaluation.ratings import (
    HumanQualityRating,
    ReviewDecision,
    aggregate_item_ratings,
)


def make_rating(
    reviewer_id: str = "rev-01",
    gp: int = 5,
    ba: int = 4,
    aq: int = 4,
    ip: int = 5,
    vp: int = 4,
    nm: int = 5,
    critical_issue: bool = False,
    decision: ReviewDecision = ReviewDecision.ACCEPT,
) -> HumanQualityRating:
    return HumanQualityRating(
        evaluation_item_id="item-001",
        reviewer_id=reviewer_id,
        garment_preservation=gp,
        body_alignment=ba,
        artifact_quality=aq,
        identity_preservation=ip,
        visual_plausibility=vp,
        non_misleading=nm,
        critical_issue=critical_issue,
        decision=decision,
    )


def test_weighted_score_calculation():
    """QUAL-001: Composite score adheres to exact rubric weighting (25/20/15/15/15/10)."""
    # 5*0.25 + 4*0.20 + 4*0.15 + 5*0.15 + 4*0.15 + 5*0.10
    # = 1.25 + 0.80 + 0.60 + 0.75 + 0.60 + 0.50 = 4.50
    rating = make_rating(gp=5, ba=4, aq=4, ip=5, vp=4, nm=5)
    assert rating.compute_weighted_score() == 4.50


def test_score_boundary_validation():
    """QUAL-002: Scores < 1 or > 5 raise ValidationError."""
    with pytest.raises(ValidationError):
        make_rating(gp=0)

    with pytest.raises(ValidationError):
        make_rating(ba=6)


def test_multi_reviewer_aggregation():
    """QUAL-003: Aggregates across multiple independent reviews."""
    r1 = make_rating("rev-01", gp=5, ba=5, aq=5, ip=5, vp=5, nm=5)  # 5.0
    r2 = make_rating("rev-02", gp=4, ba=4, aq=4, ip=4, vp=4, nm=4)  # 4.0
    r3 = make_rating("rev-03", gp=4, ba=5, aq=4, ip=5, vp=4, nm=5)  # 4.5

    agg = aggregate_item_ratings([r1, r2, r3], "item-001")
    assert agg.reviewer_count == 3
    assert agg.mean_garment_preservation == 4.33
    assert agg.has_critical_issue is False
    assert agg.consensus_decision == ReviewDecision.ACCEPT
    assert agg.disagreement_detected is False


def test_critical_issue_triggers_rejection():
    """QUAL-004: Critical issue flagged by ANY reviewer causes consensus REJECT."""
    r1 = make_rating("rev-01", gp=5, ba=5, aq=5, ip=5, vp=5, nm=5, critical_issue=False)
    r2 = make_rating(
        "rev-02",
        gp=4,
        ba=4,
        aq=2,
        ip=2,
        vp=3,
        nm=2,
        critical_issue=True,
        decision=ReviewDecision.REJECT,
    )

    agg = aggregate_item_ratings([r1, r2], "item-001")
    assert agg.has_critical_issue is True
    assert agg.consensus_decision == ReviewDecision.REJECT


def test_reviewer_disagreement_detection():
    """QUAL-005: Score spread > 1.5 triggers disagreement_detected and NEEDS_REVIEW."""
    r1 = make_rating("rev-01", gp=5)
    r2 = make_rating("rev-02", gp=3)  # spread = 2.0 > 1.5

    agg = aggregate_item_ratings([r1, r2], "item-001")
    assert agg.disagreement_detected is True
    assert agg.consensus_decision == ReviewDecision.NEEDS_REVIEW


def test_high_rejection_rate_consensus():
    """QUAL-006: 50% or more reject votes yields consensus REJECT."""
    r1 = make_rating("rev-01", decision=ReviewDecision.REJECT)
    r2 = make_rating("rev-02", decision=ReviewDecision.ACCEPT)

    agg = aggregate_item_ratings([r1, r2], "item-001")
    assert agg.rejection_rate == 0.50
    assert agg.consensus_decision == ReviewDecision.REJECT
