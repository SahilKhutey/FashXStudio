"""Personalized Product Ranking orchestration service (Phase 08.4)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fashx.ranking.cache import RankingCache, build_ranking_cache_key
from fashx.ranking.category import TaxonomyInterface
from fashx.ranking.config import get_ranking_config
from fashx.ranking.contracts import (
    RankedProductItem,
    RankedProductsResponse,
    RankingCandidate,
    RankingContext,
    RankingPagination,
    ShopperPreferenceSnapshot,
)
from fashx.ranking.eligibility import evaluate_eligibility
from fashx.ranking.enums import AvailabilityStatus, RankingReasonCode, SizeAvailability
from fashx.ranking.explanations import RANKING_REASONS, generate_ranking_reasons
from fashx.ranking.features import build_ranking_features
from fashx.ranking.scorer import FeatureValues, calculate_score, ranking_sort_key


@dataclass(frozen=True)
class RankedProduct:
    """Internal scored and tied-broken ranking entry."""

    product_id: str
    score: float
    category_score: float
    availability_freshness: float
    quality_score: float
    reasons: tuple[RankingReasonCode, ...]
    candidate: RankingCandidate
    size_availability: SizeAvailability


class PersonalizedRankingService:
    """Deterministic, eligibility-first personalized product ranking service."""

    def __init__(
        self,
        *,
        taxonomy: TaxonomyInterface,
        cache: RankingCache | None = None,
    ) -> None:
        self.taxonomy = taxonomy
        self.cache = cache or RankingCache()

    def rank(
        self,
        *,
        shopper_profile: ShopperPreferenceSnapshot,
        candidates: list[RankingCandidate],
        context: RankingContext,
        ranking_version: str = "personalized-v1",
        catalog_revision: str = "v1",
        availability_revision: str = "v1",
        use_cache: bool = True,
    ) -> RankedProductsResponse:
        """Filter eligible candidates, score deterministically, explain, and paginate."""
        config = get_ranking_config(ranking_version)
        cache_key = build_ranking_cache_key(
            shopper_id=shopper_profile.shopper_id,
            shopper_profile_revision=shopper_profile.profile_revision,
            context=context,
            ranking_version=config.ranking_version,
            config_version=config.config_version,
            taxonomy_version=self.taxonomy.version,
            catalog_revision=catalog_revision,
            availability_revision=availability_revision,
            visual_reference_hash=context.reference_image_asset_id
            or context.reference_product_id
            or "none",
        )
        if use_cache:
            cached = self.cache.get(cache_key, shopper_id=shopper_profile.shopper_id)
            if cached is not None:
                return cached.model_copy(update={"cache_hit": True})

        ranked: list[RankedProduct] = []
        for candidate in candidates:
            eligibility = evaluate_eligibility(
                candidate,
                context,
                max_age_seconds=config.max_availability_age_seconds,
            )
            if not eligibility.eligible:
                continue

            # Explicit category filter excludes unrelated products at retrieval/eligibility
            if context.category_id and context.category_id.strip() != candidate.category_id.strip():
                if not self.taxonomy.is_related(
                    context.category_id, candidate.category_id
                ) and not self.taxonomy.is_in_same_broad_category(
                    context.category_id, candidate.category_id
                ):
                    continue

            features = build_ranking_features(
                shopper_profile=shopper_profile,
                candidate=candidate,
                context=context,
                taxonomy=self.taxonomy,
                config=config,
            )
            score_res = calculate_score(
                FeatureValues(
                    category=features.category_relevance,
                    style=features.style_preference,
                    color=features.color_preference,
                    price=features.price_preference,
                    availability=features.availability_score,
                    size=features.size_availability_score,
                    visual=features.visual_similarity,
                    feedback=features.explicit_feedback_score,
                    quality=features.product_quality_score,
                ),
                config.weights,
            )
            reasons = generate_ranking_reasons(
                features,
                score_res,
                size_availability=eligibility.size_availability,
                has_category_filter=bool(context.category_id),
                has_price_preference=(
                    context.min_price is not None
                    or context.max_price is not None
                    or shopper_profile.budget_min is not None
                    or shopper_profile.budget_max is not None
                ),
            )
            ranked.append(
                RankedProduct(
                    product_id=candidate.product_id,
                    score=score_res.score,
                    category_score=features.category_relevance,
                    availability_freshness=candidate.availability_freshness,
                    quality_score=features.product_quality_score,
                    reasons=tuple(reasons),
                    candidate=candidate,
                    size_availability=eligibility.size_availability,
                )
            )

        ranked.sort(key=ranking_sort_key)

        total_eligible = len(ranked)
        start = (context.page - 1) * context.page_size
        end = start + context.page_size
        page_items = ranked[start:end]

        results = [
            RankedProductItem(
                product_id=item.product_id,
                merchant_offer_id=item.candidate.merchant_offer_id,
                title=item.candidate.title,
                category_id=item.candidate.category_id,
                price=item.candidate.price,
                currency=item.candidate.currency,
                position=start + idx + 1,
                ranking_score=item.score,
                availability=AvailabilityStatus(item.candidate.availability_status),
                size_availability=item.size_availability,
                selected_size_available=(item.size_availability == SizeAvailability.AVAILABLE),
                reasons=list(item.reasons),
                reason_labels=[RANKING_REASONS[r] for r in item.reasons],
                is_sponsored=item.candidate.is_sponsored,
                availability_verified_at=item.candidate.availability_verified_at,
                ranking_version=config.ranking_version,
            )
            for idx, item in enumerate(page_items)
        ]

        response = RankedProductsResponse(
            request_id=f"rk_{uuid4().hex[:16]}",
            ranking_version=config.ranking_version,
            config_version=config.config_version,
            taxonomy_version=self.taxonomy.version,
            cache_hit=False,
            results=results,
            pagination=RankingPagination(
                page=context.page,
                page_size=context.page_size,
                total_eligible=total_eligible,
                has_more=end < total_eligible,
            ),
        )
        if use_cache:
            self.cache.set(
                cache_key,
                response,
                shopper_id=shopper_profile.shopper_id,
                ttl_seconds=config.cache_ttl_seconds,
            )
        return response
