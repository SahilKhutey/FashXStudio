from abc import ABC, abstractmethod

from .entities import RecommendationCandidate


class RecommendationCandidateRepository(ABC):
    @abstractmethod
    async def add(
        self,
        candidate: RecommendationCandidate,
    ) -> RecommendationCandidate:
        raise NotImplementedError

    @abstractmethod
    async def list_candidates(
        self,
        *,
        category: str | None = None,
        brand: str | None = None,
        region: str | None = None,
    ) -> list[RecommendationCandidate]:
        raise NotImplementedError
