from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import select

from database.models.catalog import Brand
from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError
from fashx.discovery.taste import SignalEvent, compute_taste_vector
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
    title: str = ""
    brand: str = ""
    image_url: str | None = None
    price_updated_at: Any = None
    reason_chips: list[str] = field(default_factory=list)
    tryon_supported: bool = True


@dataclass
class GenerateFeedResult:
    user_id: UUID
    items: list[FeedItemResult] = field(default_factory=list)
    total_candidates: int = 0
    filtered_candidates: int = 0
    empty_reason: str | None = None
    relaxed: list[str] = field(default_factory=list)


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
        # 1. Fetch User Profile, Preferences & Interaction Signals
        user_styles: list[str] | None = None
        raw_signals: list[tuple[UUID, str, datetime | None]] = []
        now = datetime.now(UTC)

        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            body = await self.profile_uow.body_profiles.get_by_user_id(cmd.user_id)
            pref = await self.profile_uow.preferences.get_by_user_id(cmd.user_id)
            active_photo = await self.profile_uow.photos.get_active_photo(
                cmd.user_id, "tryon_reference"
            )

            # Style quiz archetype preferences
            try:
                onboarding = await self.profile_uow.onboarding_profiles.get_by_user_id(cmd.user_id)
                if onboarding and onboarding.styles:
                    user_styles = list(onboarding.styles)
            except Exception:
                pass

            # Feed interaction signals (likes, hides, not_interested)
            try:
                from database.models.feed import FeedSignal

                res_sig = await self.profile_uow.session.scalars(
                    select(FeedSignal).where(FeedSignal.user_id == cmd.user_id)
                )
                for s in res_sig.all():
                    raw_signals.append((s.garment_id, s.action, s.created_at))
            except Exception:
                pass

            # Saved wardrobe items (positive interaction signal)
            try:
                from database.models.commerce_feedback import WardrobeItem

                res_w = await self.profile_uow.session.scalars(
                    select(WardrobeItem).where(WardrobeItem.user_id == cmd.user_id)
                )
                for w in res_w.all():
                    raw_signals.append((w.garment_id, "like", w.saved_at))
            except Exception:
                pass

            user_build = body.build if body else "regular"
            undertone = "neutral"
            if active_photo:
                undertone = "warm"

            budget_min = pref.budget_min if pref else None
            budget_max = pref.budget_max if pref else None
            favored_colors = list(pref.colors_favored) if pref and pref.colors_favored else []
            avoided_colors = list(pref.colors_avoided) if pref and pref.colors_avoided else []
            allowed_categories = list(pref.categories) if pref and pref.categories else None

        # 2. Fetch Catalog Candidates (Gated: cleared sources + active products)
        embedder = FakeEmbedder()
        async with self.catalog_uow:
            # Resolve garment embeddings for raw interaction signals
            signal_events: list[SignalEvent] = []
            for g_id, action, dt in raw_signals:
                try:
                    enrichment = await self.catalog_uow.enrichments.get_by_garment_id(g_id)
                    if enrichment and enrichment.embedding:
                        emb = enrichment.embedding
                    else:
                        g_obj = await self.catalog_uow.canonical_garments.get_by_id(g_id)
                        title = g_obj.display_name if g_obj else "garment"
                        emb = embedder.embed_text([title])[0]
                    signal_events.append(
                        SignalEvent(
                            garment_id=str(g_id),
                            action=action,
                            timestamp=dt or now,
                            embedding=np.array(emb, dtype=np.float32),
                        )
                    )
                except Exception:
                    continue

            # Compute taste vector blending cold-start archetypes with interaction signals
            taste_vector = compute_taste_vector(signal_events, user_styles=user_styles, now=now)
            taste_vector_list = taste_vector.tolist()

            garments = await self.catalog_uow.canonical_garments.list_feed_candidates(limit=200)
            candidates: list[CandidateItem] = []

            for g in garments:
                offers = await self.catalog_uow.offers.list_for_garment(g.id)
                if not offers:
                    continue
                top_offer = offers[0]
                enrichment = await self.catalog_uow.enrichments.get_by_garment_id(g.id)
                attrs = enrichment.attributes_json if enrichment else {}
                emb = enrichment.embedding if enrichment else None

                brand_name = ""
                if g.brand_id:
                    brand_obj = await self.catalog_uow.session.get(Brand, g.brand_id)
                    if brand_obj:
                        brand_name = brand_obj.name

                images_rec = await self.catalog_uow.images.list_for_garment(g.id)
                image_url = images_rec[0].image_url if images_rec and images_rec[0].image_url else None
                title = g.display_name or f"{g.category.capitalize()} {g.subcategory or ''}".strip()
                tryon_supported = bool(getattr(g, "tryon_supported", True))
                price_updated_at = getattr(top_offer, "price_checked_at", None) or getattr(top_offer, "updated_at", None)

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
                        title=title,
                        brand=brand_name,
                        image_url=image_url,
                        price_updated_at=price_updated_at,
                        tryon_supported=tryon_supported,
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

        # 4. Stage 2: Explicit preference, compatibility, and taste vector scoring
        scored_items: list[ScoredItem] = []
        has_taste_signal = bool(user_styles or signal_events)

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

            if has_taste_signal:
                cand_emb = cand.embedding
                if not cand_emb:
                    cand_emb = embedder.embed_text(
                        [f"{cand.title} {cand.category} {cand.subcategory or ''}"]
                    )[0]
                taste_sim = cosine_similarity(taste_vector_list, cand_emb)
                # Blend compatibility (50%) with personalized taste similarity (50%)
                relevance = round(0.5 * compat.total_score + 0.5 * taste_sim, 3)
            else:
                relevance = round(compat.total_score, 3)

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
            reason_chips = []
            if s.item.category:
                reason_chips.append(s.item.category.capitalize())
            if s.item.dominant_color:
                reason_chips.append(s.item.dominant_color.capitalize())
            elif s.item.silhouette:
                reason_chips.append(s.item.silhouette.replace("_", " ").capitalize())

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
                    title=s.item.title,
                    brand=s.item.brand,
                    image_url=s.item.image_url,
                    price_updated_at=s.item.price_updated_at,
                    reason_chips=reason_chips[:2],
                    tryon_supported=s.item.tryon_supported,
                )
            )

        empty_reason = None
        if not feed_items:
            empty_reason = "catalog_empty" if total_candidates == 0 else "no_matches_in_size_or_budget"

        return GenerateFeedResult(
            user_id=cmd.user_id,
            items=feed_items,
            total_candidates=total_candidates,
            filtered_candidates=filtered_count,
            empty_reason=empty_reason,
        )
