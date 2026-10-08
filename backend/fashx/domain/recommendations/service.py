from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fashx.core.event_bus import EventBus

from .entities import (
    RecommendationExplanation,
    RecommendationItem,
    RecommendationResult,
)
from .enums import RecommendationReason
from .events import RecommendationsGenerated
from .provider import PersonalizationProvider
from .ranking import (
    calculate_score,
    rank_candidates,
)
from .recommendation_context import RecommendationContext
from .repository import (
    RecommendationCandidateRepository,
)


@dataclass(slots=True)
class RecommendationService:
    candidate_repository: RecommendationCandidateRepository
    personalization_provider: PersonalizationProvider
    event_bus: EventBus | None = None

    async def recommend(
        self,
        *,
        context: RecommendationContext,
    ) -> RecommendationResult:
        context.validate()

        candidates = await self.candidate_repository.list_candidates(
            category=context.category,
            brand=context.brand,
            region=context.region,
        )

        candidates = [
            candidate
            for candidate in candidates
            if candidate.product_id not in context.exclude_product_ids
        ]

        scored = []

        for candidate in candidates:
            personalization = Decimal("0")

            if context.customer_id is not None:
                personalization = await self.personalization_provider.score(
                    context.customer_id,
                    category=candidate.category,
                    brand=candidate.brand,
                    style=candidate.style,
                    color=candidate.color,
                    material=candidate.material,
                    occasion=candidate.occasion,
                    region=context.region,
                )

            contextual = Decimal("0")

            if context.category:
                contextual += (
                    Decimal("0.5")
                    if candidate.category
                    and candidate.category.lower() == context.category.lower()
                    else Decimal("0")
                )

            if context.style:
                contextual += (
                    Decimal("0.5")
                    if candidate.style
                    and candidate.style.lower() == context.style.lower()
                    else Decimal("0")
                )

            contextual = min(Decimal("1"), contextual)

            price = (
                Decimal("1")
                if (
                    candidate.price is not None
                    and (
                        context.min_price is None
                        or candidate.price >= context.min_price
                    )
                    and (
                        context.max_price is None
                        or candidate.price <= context.max_price
                    )
                )
                else Decimal("0")
            )

            region = (
                Decimal("1")
                if (
                    candidate.region is None
                    or context.region is None
                    or candidate.region.lower() == context.region.lower()
                )
                else Decimal("0")
            )

            source = Decimal("1")

            final_score = calculate_score(
                personalization=personalization,
                context=contextual,
                price=price,
                region=region,
                source=source,
            )

            scored.append((candidate, final_score))

        ranked = rank_candidates(scored)
        limited = ranked[: context.limit]

        items = []

        for rank, (candidate, score) in enumerate(limited, start=1):
            explanations: list[RecommendationExplanation] = []

            if candidate.style and context.style:
                if candidate.style.lower() == context.style.lower():
                    explanations.append(
                        RecommendationExplanation(
                            reason=RecommendationReason.STYLE_MATCH,
                            score=score,
                            message="Matches requested style.",
                        )
                    )

            if candidate.category and context.category:
                if candidate.category.lower() == context.category.lower():
                    explanations.append(
                        RecommendationExplanation(
                            reason=RecommendationReason.CATEGORY_MATCH,
                            score=score,
                            message="Matches requested category.",
                        )
                    )

            if candidate.brand and context.brand:
                if candidate.brand.lower() == context.brand.lower():
                    explanations.append(
                        RecommendationExplanation(
                            reason=RecommendationReason.BRAND_MATCH,
                            score=score,
                            message="Matches requested brand.",
                        )
                    )

            if candidate.color and context.color:
                if candidate.color.lower() == context.color.lower():
                    explanations.append(
                        RecommendationExplanation(
                            reason=RecommendationReason.COLOR_MATCH,
                            score=score,
                            message="Matches requested color.",
                        )
                    )

            items.append(
                RecommendationItem(
                    product_id=candidate.product_id,
                    variant_id=candidate.variant_id,
                    listing_id=candidate.listing_id,
                    score=score,
                    rank=rank,
                    explanations=tuple(explanations),
                )
            )

        result = RecommendationResult(
            items=tuple(items),
            total_candidates=len(candidates),
        )

        if self.event_bus is not None:
            await self.event_bus.publish(
                RecommendationsGenerated(
                    customer_id=context.customer_id,
                    result_count=len(result.items),
                )
            )

        return result
