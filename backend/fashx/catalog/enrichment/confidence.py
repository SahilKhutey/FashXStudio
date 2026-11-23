from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import ReviewFlag, ReviewStatus

LOW_RISK_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "garment_type",
        "color",
        "fit_type",
        "pattern",
        "sleeve_type",
        "neckline",
        "intended_audience",
    }
)

SENSITIVE_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "fabric",
        "fabric_blend",
        "fabric_composition",
        "occasion",
        "style_family",
    }
)


@dataclass(frozen=True)
class ReviewDecision:
    review_required: bool
    review_status: ReviewStatus
    review_reasons: list[str] = field(default_factory=list)
    flags: list[ReviewFlag] = field(default_factory=list)


def decide_review(
    attribute_id: str,
    confidence: float | None,
    *,
    evidence_present: bool,
    conflicting: bool = False,
    is_source_only: bool = False,
) -> ReviewDecision:
    """Evaluate confidence and evidence against policy thresholds (Section 6.2.11 & 6.2.13)."""
    if conflicting:
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=["CONFLICTING_EVIDENCE"],
            flags=[ReviewFlag.CONFLICTING_EVIDENCE],
        )

    if not evidence_present:
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=["MISSING_EVIDENCE"],
            flags=[ReviewFlag.MISSING_EVIDENCE],
        )

    if confidence is None:
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=["MISSING_CONFIDENCE"],
            flags=[ReviewFlag.LOW_CONFIDENCE],
        )

    if confidence < 0.60:
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=[f"LOW_CONFIDENCE_{confidence:.2f}"],
            flags=[ReviewFlag.LOW_CONFIDENCE],
        )

    if 0.60 <= confidence < 0.80:
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=[f"MEDIUM_CONFIDENCE_{confidence:.2f}"],
            flags=[ReviewFlag.LOW_CONFIDENCE],
        )

    if 0.80 <= confidence < 0.95:
        if attribute_id in LOW_RISK_ATTRIBUTES:
            return ReviewDecision(
                review_required=False,
                review_status=ReviewStatus.AUTO_ACCEPTED,
                review_reasons=[],
                flags=[],
            )
        return ReviewDecision(
            review_required=True,
            review_status=ReviewStatus.PENDING_REVIEW,
            review_reasons=[f"SENSITIVE_ATTRIBUTE_CONFIDENCE_{confidence:.2f}"],
            flags=[ReviewFlag.LOW_CONFIDENCE],
        )

    # 0.95 - 1.00: High confidence auto-accept eligible
    return ReviewDecision(
        review_required=False,
        review_status=ReviewStatus.AUTO_ACCEPTED,
        review_reasons=[],
        flags=[],
    )
