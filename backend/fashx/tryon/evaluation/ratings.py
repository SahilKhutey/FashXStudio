"""Human visual quality rating models, rubric weighting, and multi-reviewer consensus.

Rubric Weights (Total 100%):
1. Garment preservation: 25%
2. Body alignment: 20%
3. Artifact quality: 15%
4. Identity preservation: 15%
5. Visual plausibility: 15%
6. Non-misleading representation: 10%

Hard Gates:
If critical_issue is True, or if identity/misleading scores fall below 2,
the item fails regardless of how high other dimensions score.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

RUBRIC_WEIGHTS: dict[str, float] = {
    "garment_preservation": 0.25,
    "body_alignment": 0.20,
    "artifact_quality": 0.15,
    "identity_preservation": 0.15,
    "visual_plausibility": 0.15,
    "non_misleading": 0.10,
}


class ReviewDecision(str, Enum):
    ACCEPT = "ACCEPT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECT = "REJECT"


class HumanQualityRating(BaseModel):
    """Evaluation scorecard completed by an independent reviewer."""

    model_config = ConfigDict(extra="forbid")

    evaluation_item_id: str = Field(..., description="Target evaluated item ID")
    reviewer_id: str = Field(..., description="Authenticated reviewer identifier")
    garment_preservation: int = Field(
        ..., ge=1, le=5, description="Fidelity of colors, prints, cuts (1..5)"
    )
    body_alignment: int = Field(
        ..., ge=1, le=5, description="Anatomical placement and symmetry (1..5)"
    )
    artifact_quality: int = Field(
        ..., ge=1, le=5, description="Absence of blur, extra limbs, distortions (1..5)"
    )
    identity_preservation: int = Field(
        ..., ge=1, le=5, description="Preservation of shopper face, tone, features (1..5)"
    )
    visual_plausibility: int = Field(
        ..., ge=1, le=5, description="Natural photographic realism and lighting (1..5)"
    )
    non_misleading: int = Field(
        ..., ge=1, le=5, description="Freedom from false impressions of fit or shape (1..5)"
    )
    critical_issue: bool = Field(
        default=False, description="Flagged for fatal flaws (identity distortion, false sizing)"
    )
    decision: ReviewDecision = Field(..., description="Overall reviewer verdict")
    notes: str | None = Field(
        default=None, max_length=2000, description="Optional reviewer remarks"
    )

    def compute_weighted_score(self) -> float:
        """Calculate weighted composite quality score (1.00 to 5.00)."""
        score = (
            self.garment_preservation * RUBRIC_WEIGHTS["garment_preservation"]
            + self.body_alignment * RUBRIC_WEIGHTS["body_alignment"]
            + self.artifact_quality * RUBRIC_WEIGHTS["artifact_quality"]
            + self.identity_preservation * RUBRIC_WEIGHTS["identity_preservation"]
            + self.visual_plausibility * RUBRIC_WEIGHTS["visual_plausibility"]
            + self.non_misleading * RUBRIC_WEIGHTS["non_misleading"]
        )
        return round(score, 2)


@dataclass(frozen=True)
class AggregatedItemRating:
    """Consolidated ratings across multiple independent reviewers for a single item."""

    evaluation_item_id: str
    reviewer_count: int
    mean_garment_preservation: float
    mean_body_alignment: float
    mean_artifact_quality: float
    mean_identity_preservation: float
    mean_visual_plausibility: float
    mean_non_misleading: float
    mean_weighted_score: float
    has_critical_issue: bool
    rejection_rate: float
    consensus_decision: ReviewDecision
    disagreement_detected: bool


def aggregate_item_ratings(
    ratings: list[HumanQualityRating],
    item_id: str,
) -> AggregatedItemRating:
    """Aggregate individual reviews and detect significant rater disagreement."""
    if not ratings:
        raise ValueError("Cannot aggregate empty ratings list")

    count = len(ratings)
    gp_list = [r.garment_preservation for r in ratings]
    ba_list = [r.body_alignment for r in ratings]
    aq_list = [r.artifact_quality for r in ratings]
    ip_list = [r.identity_preservation for r in ratings]
    vp_list = [r.visual_plausibility for r in ratings]
    nm_list = [r.non_misleading for r in ratings]
    scores = [r.compute_weighted_score() for r in ratings]

    has_crit = any(r.critical_issue for r in ratings)
    reject_count = sum(1 for r in ratings if r.decision == ReviewDecision.REJECT)
    rejection_rate = round(reject_count / count, 2)

    # Detect divergence: spread of > 1.5 in any dimension indicates disagreement
    divergences = [
        max(gp_list) - min(gp_list),
        max(ba_list) - min(ba_list),
        max(aq_list) - min(aq_list),
        max(ip_list) - min(ip_list),
        max(vp_list) - min(vp_list),
        max(nm_list) - min(nm_list),
    ]
    disagreement = any(d > 1.5 for d in divergences)

    # Determine consensus decision
    if has_crit or rejection_rate >= 0.5:
        consensus = ReviewDecision.REJECT
    elif disagreement or any(r.decision == ReviewDecision.NEEDS_REVIEW for r in ratings):
        consensus = ReviewDecision.NEEDS_REVIEW
    else:
        consensus = ReviewDecision.ACCEPT

    return AggregatedItemRating(
        evaluation_item_id=item_id,
        reviewer_count=count,
        mean_garment_preservation=round(statistics.mean(gp_list), 2),
        mean_body_alignment=round(statistics.mean(ba_list), 2),
        mean_artifact_quality=round(statistics.mean(aq_list), 2),
        mean_identity_preservation=round(statistics.mean(ip_list), 2),
        mean_visual_plausibility=round(statistics.mean(vp_list), 2),
        mean_non_misleading=round(statistics.mean(nm_list), 2),
        mean_weighted_score=round(statistics.mean(scores), 2),
        has_critical_issue=has_crit,
        rejection_rate=rejection_rate,
        consensus_decision=consensus,
        disagreement_detected=disagreement,
    )
