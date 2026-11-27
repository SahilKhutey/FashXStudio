"""Evidence-backed ranking explanations without fit-guarantee claims (Task 8.4.12)."""

from __future__ import annotations

from fashx.ranking.contracts import RankingFeatures
from fashx.ranking.enums import RankingReasonCode, SizeAvailability
from fashx.ranking.scorer import ScoreResult

RANKING_REASONS: dict[RankingReasonCode, str] = {
    RankingReasonCode.CATEGORY_MATCH: "Matches your selected category",
    RankingReasonCode.STYLE_MATCH: "Matches your preferred style",
    RankingReasonCode.COLOR_MATCH: "Matches your preferred colours",
    RankingReasonCode.PRICE_MATCH: "Within your preferred price range",
    RankingReasonCode.SIZE_AVAILABLE: "Available in your selected size",
    RankingReasonCode.VISUAL_SIMILARITY: "Similar to a product you selected",
    RankingReasonCode.FEEDBACK_MATCH: "Based on products you liked",
    RankingReasonCode.QUALITY_VALIDATED: "Meets product quality requirements",
}


def generate_ranking_reasons(
    features: RankingFeatures,
    score: ScoreResult,
    *,
    size_availability: SizeAvailability,
    has_category_filter: bool = False,
    has_price_preference: bool = False,
    max_reasons: int = 5,
) -> list[RankingReasonCode]:
    """Select strongest evidence-backed reason codes for a ranked product.

    Never emits ``SIZE_AVAILABLE`` unless the selected size is confirmed
    available, and never emits reason codes lacking positive feature evidence.
    """
    candidates: list[tuple[float, RankingReasonCode]] = []

    if has_category_filter and features.category_relevance >= 0.65:
        candidates.append(
            (score.contributions.get("category", 0.0), RankingReasonCode.CATEGORY_MATCH)
        )
    if features.style_preference >= 0.70 and "style" in score.contributions:
        candidates.append(
            (score.contributions["style"], RankingReasonCode.STYLE_MATCH)
        )
    if features.color_preference >= 0.75 and "color" in score.contributions:
        candidates.append(
            (score.contributions["color"], RankingReasonCode.COLOR_MATCH)
        )
    if has_price_preference and features.price_preference >= 0.75 and "price" in score.contributions:
        candidates.append(
            (score.contributions["price"], RankingReasonCode.PRICE_MATCH)
        )
    if size_availability == SizeAvailability.AVAILABLE and (
        features.size_availability_score is not None and features.size_availability_score >= 1.0
    ):
        candidates.append(
            (score.contributions.get("size", 0.1), RankingReasonCode.SIZE_AVAILABLE)
        )
    if features.visual_similarity is not None and features.visual_similarity >= 0.70:
        candidates.append(
            (score.contributions.get("visual", 0.0), RankingReasonCode.VISUAL_SIMILARITY)
        )
    if features.explicit_feedback_score >= 0.75 and "feedback" in score.contributions:
        candidates.append(
            (score.contributions["feedback"], RankingReasonCode.FEEDBACK_MATCH)
        )
    if features.product_quality_score >= 0.75 and "quality" in score.contributions:
        candidates.append(
            (score.contributions["quality"], RankingReasonCode.QUALITY_VALIDATED)
        )

    candidates.sort(key=lambda pair: (-pair[0], pair[1].value))
    return [code for _, code in candidates[:max_reasons]]
