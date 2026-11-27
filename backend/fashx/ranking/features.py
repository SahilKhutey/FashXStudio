"""Feature builder assembling normalized feature values and provenance (Task 8.4.1)."""

from __future__ import annotations

from fashx.ranking.availability import availability_score
from fashx.ranking.category import TaxonomyInterface, category_score
from fashx.ranking.color import color_preference_score
from fashx.ranking.config import RankingConfig
from fashx.ranking.contracts import (
    FeatureProvenance,
    RankingCandidate,
    RankingContext,
    RankingFeatures,
    ShopperPreferenceSnapshot,
)
from fashx.ranking.enums import SizeAvailability
from fashx.ranking.feedback import explicit_feedback_score
from fashx.ranking.price import price_preference_score
from fashx.ranking.quality import combined_quality_score
from fashx.ranking.size import check_size_availability
from fashx.ranking.style import style_preference_score
from fashx.ranking.visual_similarity import compute_visual_similarity


def build_ranking_features(
    shopper_profile: ShopperPreferenceSnapshot,
    candidate: RankingCandidate,
    context: RankingContext,
    taxonomy: TaxonomyInterface,
    config: RankingConfig,
) -> RankingFeatures:
    """Build normalized [0.0, 1.0] ranking features with full provenance."""
    cat_val = category_score(context.category_id, candidate.category_id, taxonomy)
    style_val = style_preference_score(
        candidate.style_tags,
        shopper_profile.liked_styles,
        shopper_profile.disliked_styles,
        min_confidence=config.min_attribute_confidence,
    )
    color_val = color_preference_score(
        candidate.primary_colors,
        shopper_profile.preferred_colors,
        shopper_profile.disliked_colors,
        secondary_colors=candidate.secondary_colors,
        color_confidences=candidate.color_confidences,
        min_confidence=config.min_attribute_confidence,
    )

    budget_min = (
        context.min_price if context.min_price is not None else shopper_profile.budget_min
    )
    budget_max = (
        context.max_price if context.max_price is not None else shopper_profile.budget_max
    )
    price_val = price_preference_score(
        candidate.price,
        budget_min,
        budget_max,
        offer_currency=candidate.currency,
        target_currency=context.currency,
    )

    avail_val = availability_score(
        candidate, max_age_seconds=config.max_availability_age_seconds
    )

    size_status = check_size_availability(context.selected_size, candidate.variants)
    size_val: float | None
    if size_status == SizeAvailability.NOT_APPLICABLE:
        size_val = None
    elif size_status == SizeAvailability.AVAILABLE:
        size_val = 1.0
    elif size_status == SizeAvailability.UNKNOWN:
        size_val = 0.25
    else:
        size_val = 0.0

    visual_val: float | None = None
    if shopper_profile.reference_embedding is not None and candidate.embedding is not None:
        try:
            visual_val = compute_visual_similarity(
                shopper_profile.reference_embedding,
                candidate.embedding,
                reference_model=shopper_profile.reference_embedding_model,
                candidate_model=candidate.embedding_model,
                reference_version=shopper_profile.reference_embedding_version,
                candidate_version=candidate.embedding_version,
                reference_preprocessing_version=shopper_profile.reference_preprocessing_version,
                candidate_preprocessing_version=candidate.preprocessing_version,
                permission_granted=shopper_profile.reference_permission_granted,
                lower_bound=config.visual_similarity_lower_bound,
                upper_bound=config.visual_similarity_upper_bound,
            )
        except (ValueError, PermissionError):
            visual_val = None

    fb_events = shopper_profile.feedback_by_product.get(candidate.product_id, [])
    fb_val = explicit_feedback_score(fb_events)
    quality_val = combined_quality_score(candidate)

    provenance = (
        FeatureProvenance("category_relevance", cat_val, f"taxonomy:{taxonomy.version}"),
        FeatureProvenance(
            "style_preference",
            style_val,
            f"shopper_profile_rev:{shopper_profile.profile_revision}",
        ),
        FeatureProvenance(
            "color_preference",
            color_val,
            f"shopper_profile_rev:{shopper_profile.profile_revision}",
        ),
        FeatureProvenance("price_preference", price_val, f"offer:{candidate.merchant_offer_id}"),
        FeatureProvenance("availability_score", avail_val, f"offer:{candidate.merchant_offer_id}"),
        FeatureProvenance("size_availability_score", size_val, f"variants:{candidate.product_id}"),
        FeatureProvenance(
            "visual_similarity",
            visual_val,
            f"embedding:{candidate.embedding_model or 'none'}@{candidate.embedding_version or 'none'}",
        ),
        FeatureProvenance(
            "explicit_feedback_score", fb_val, f"feedback_events:{len(fb_events)}"
        ),
        FeatureProvenance("quality_score", quality_val, f"merchant:{candidate.merchant_id}"),
    )

    return RankingFeatures(
        category_relevance=cat_val,
        style_preference=style_val,
        color_preference=color_val,
        price_preference=price_val,
        availability_score=avail_val,
        size_availability_score=size_val,
        visual_similarity=visual_val,
        explicit_feedback_score=fb_val,
        product_quality_score=quality_val,
        merchant_quality_score=quality_val,
        provenance=provenance,
    )
