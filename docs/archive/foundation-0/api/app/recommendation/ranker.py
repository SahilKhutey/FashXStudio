import math
from dataclasses import dataclass

from .compatibility import CompatibilityScore
from .filters import CandidateItem


def cosine_similarity(v1: list[float] | None, v2: list[float] | None) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.5
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


def item_redundancy(item1: CandidateItem, item2: CandidateItem) -> float:
    """Measure how redundant/similar two items are (used for MMR diversity penalty)."""
    score = 0.0
    if item1.category == item2.category:
        score += 0.4
    if item1.subcategory and item1.subcategory == item2.subcategory:
        score += 0.3
    if item1.dominant_color and item1.dominant_color == item2.dominant_color:
        score += 0.2
    if item1.silhouette and item1.silhouette == item2.silhouette:
        score += 0.1
    return min(1.0, score)


@dataclass
class ScoredItem:
    item: CandidateItem
    compatibility: CompatibilityScore
    relevance_score: float


class PersonalizedRanker:
    """Stage 3: Ranks candidates using relevance scoring and Maximal Marginal Relevance (MMR) for diversity."""

    @classmethod
    def rank_and_diversify(
        cls,
        scored_items: list[ScoredItem],
        top_k: int = 20,
        diversity_lambda: float = 0.7,
    ) -> list[ScoredItem]:
        r"""Apply Maximal Marginal Relevance (MMR) to balance relevance with diversity.

        Formula:
            MMR = argmax_{d in R \ S} [ lambda * Rel(d) - (1 - lambda) * max_{s in S} Redundancy(d, s) ]
        """
        if not scored_items:
            return []

        remaining = list(scored_items)
        selected: list[ScoredItem] = []

        # 1. Pick the single highest-scoring item first
        remaining.sort(key=lambda s: s.relevance_score, reverse=True)
        first_item = remaining.pop(0)
        selected.append(first_item)

        # 2. Greedily pick next items balancing relevance and novelty
        while remaining and len(selected) < top_k:
            best_score = -float("inf")
            best_idx = 0

            for idx, cand in enumerate(remaining):
                relevance = cand.relevance_score
                # Max similarity to already selected items
                max_sim = max(item_redundancy(cand.item, sel.item) for sel in selected)
                mmr_val = (diversity_lambda * relevance) - ((1.0 - diversity_lambda) * max_sim)

                if mmr_val > best_score:
                    best_score = mmr_val
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        return selected
