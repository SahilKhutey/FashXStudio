"""Offline ranking evaluation dataset contracts (Task 8.4.14)."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.ranking.contracts import (
    RankingCandidate,
    RankingContext,
    ShopperPreferenceSnapshot,
)


@dataclass(frozen=True)
class JudgedQueryPair:
    """Single manually judged query-product relevance item."""

    query_id: str
    shopper_profile: ShopperPreferenceSnapshot
    context: RankingContext
    candidates: tuple[RankingCandidate, ...]
    relevance_grades: dict[str, int]  # product_id -> {0, 1, 2, 3}
    disliked_product_ids: frozenset[str] = frozenset()
