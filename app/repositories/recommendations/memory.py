from app.domain.recommendations.entities import (
    RecommendationCandidate,
)
from app.domain.recommendations.repository import (
    RecommendationCandidateRepository,
)


class InMemoryRecommendationCandidateRepository(
    RecommendationCandidateRepository
):
    def __init__(self) -> None:
        self._items: list[RecommendationCandidate] = []

    async def add(
        self,
        candidate: RecommendationCandidate,
    ) -> RecommendationCandidate:
        candidate.validate()
        self._items.append(candidate)
        return candidate

    async def list_candidates(
        self,
        *,
        category: str | None = None,
        brand: str | None = None,
        region: str | None = None,
    ) -> list[RecommendationCandidate]:
        result = self._items

        if category:
            result = [
                item
                for item in result
                if item.category
                and item.category.lower() == category.lower()
            ]

        if brand:
            result = [
                item
                for item in result
                if item.brand and item.brand.lower() == brand.lower()
            ]

        if region:
            result = [
                item
                for item in result
                if item.region is None or item.region.lower() == region.lower()
            ]

        return list(result)
