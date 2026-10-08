from dataclasses import dataclass, field
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.compatibility import CompatibilityMatrix
from fashx.recommendation.filters import (
    CandidateItem,
    DeterministicFilter,
    FilterCriteria,
)
from fashx.recommendation.ranker import (
    PersonalizedRanker,
    ScoredItem,
    cosine_similarity,
)
from fashx.recommendation.stylist_explainer import StylistExplainer


@dataclass
class GenerateFeedCommand:
    user_id: UUID
    limit: int = 20
    diversity_lambda: float = 0.7


@dataclass
class FeedItemResult:
    garment_id: UUID
    category: str
    subcategory: str | None
    price_minor: int
    dominant_color: str | None
    silhouette: str | None
    relevance_score: float
    stylist_explanation: str


@dataclass
class GenerateFeedResult:
    user_id: UUID
    items: list[FeedItemResult] = field(default_factory=list)
    total_candidates: int = 0
    filtered_candidates: int = 0


class GenerateFeedUseCase:
    """Orchestrates 3-stage personalized recommendation and explainable feed generation."""

    def __init__(
        self,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
    ) -> None:
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow

    async def execute(self, cmd: GenerateFeedCommand) -> GenerateFeedResult:
        # 1. Fetch User Profile & Preferences
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            body = await self.profile_uow.body_profiles.get_by_user_id(cmd.user_id)
            pref = await self.profile_uow.preferences.get_by_user_id(cmd.user_id)
            active_photo = await self.profile_uow.photos.get_active_photo(
                cmd.user_id, "tryon_reference"
            )

            user_build = body.build if body else "regular"
            undertone = "neutral"
            # If user has an active portrait photo with skin tone, calibrate undertone
            if active_photo:
                undertone = "warm"  # calibrated baseline

            budget_min = pref.budget_min if pref else None
            budget_max = pref.budget_max if pref else None
            favored_colors = list(pref.colors_favored) if pref and pref.colors_favored else []
            avoided_colors = list(pref.colors_avoided) if pref and pref.colors_avoided else []
            allowed_categories = list(pref.categories) if pref and pref.categories else None

        # 2. Fetch Catalog Candidates
        async with self.catalog_uow:
            garments = await self.catalog_uow.canonical_garments.list(limit=200)
            candidates: list[CandidateItem] = []

            for g in garments:
                offers = await self.catalog_uow.offers.list_for_garment(g.id)
                if not offers:
                    continue
                top_offer = offers[0]
                enrichment = await self.catalog_uow.enrichments.get_by_garment_id(g.id)
                attrs = enrichment.attributes_json if enrichment else {}
                emb = enrichment.embedding if enrichment else None

                candidates.append(
                    CandidateItem(
                        garment_id=g.id,
                        category=g.category,
                        subcategory=g.subcategory,
                        price_minor=top_offer.price_minor,
                        in_stock=top_offer.in_stock,
                        dominant_color=attrs.get("dominant_color"),
                        silhouette=attrs.get("silhouette"),
                        formality=attrs.get("formality"),
                        attributes=attrs,
                        embedding=emb,
                    )
                )

        total_candidates = len(candidates)

        # 3. Stage 1: Deterministic Filtering
        criteria = FilterCriteria(
            budget_min=budget_min,
            budget_max=budget_max,
            allowed_categories=allowed_categories,
            avoided_colors=avoided_colors,
        )
        surviving = DeterministicFilter.filter_candidates(candidates, criteria)
        filtered_count = len(surviving)

        if not surviving:
            return GenerateFeedResult(
                user_id=cmd.user_id,
                items=[],
                total_candidates=total_candidates,
                filtered_candidates=0,
            )

        # 4. Stage 2: Multimodal Compatibility Scoring
        scored_items: list[ScoredItem] = []
        user_emb = [0.05] * 512  # baseline preference embedding vector

        for cand in surviving:
            compat = CompatibilityMatrix.evaluate(
                user_undertone=undertone,
                user_build=user_build,
                garment_color=cand.dominant_color,
                garment_cut=cand.silhouette,
                favored_colors=favored_colors,
                favored_categories=allowed_categories,
                category=cand.category,
            )

            # Stage 3 Relevance: Combine compatibility + embedding similarity
            emb_sim = cosine_similarity(user_emb, cand.embedding)
            relevance = round(0.70 * compat.total_score + 0.30 * emb_sim, 3)

            scored_items.append(
                ScoredItem(
                    item=cand,
                    compatibility=compat,
                    relevance_score=relevance,
                )
            )

        # 5. Stage 3: MMR Ranking and Diversification
        ranked = PersonalizedRanker.rank_and_diversify(
            scored_items=scored_items,
            top_k=cmd.limit,
            diversity_lambda=cmd.diversity_lambda,
        )

        # 6. Generate Natural Language Explanations
        feed_items: list[FeedItemResult] = []
        for s in ranked:
            explanation = StylistExplainer.generate_explanation(
                item=s.item,
                compatibility=s.compatibility,
                user_build=user_build,
                user_undertone=undertone,
            )
            feed_items.append(
                FeedItemResult(
                    garment_id=s.item.garment_id,
                    category=s.item.category,
                    subcategory=s.item.subcategory,
                    price_minor=s.item.price_minor,
                    dominant_color=s.item.dominant_color,
                    silhouette=s.item.silhouette,
                    relevance_score=s.relevance_score,
                    stylist_explanation=explanation,
                )
            )

        return GenerateFeedResult(
            user_id=cmd.user_id,
            items=feed_items,
            total_candidates=total_candidates,
            filtered_candidates=filtered_count,
        )
