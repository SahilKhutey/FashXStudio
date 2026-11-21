from __future__ import annotations

from collections import defaultdict
from uuid import UUID

DEFAULT_WEIGHTS: dict[str, float] = {
    "keyword": 1.0,
    "semantic": 0.8,
    "visual": 0.7,
}


def merge_candidates_rrf(
    stream_results: dict[str, list[tuple[UUID, float]]],
    weights: dict[str, float] | None = None,
    k: int = 60,
) -> list[tuple[UUID, float]]:
    """Merge ranked candidate lists from multiple retrieval streams using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF(d) = sum_{m in M} ( w_m / (k + rank_m(d)) )

    where rank_m(d) is the 1-based position of candidate d in stream m.
    """
    if not stream_results:
        return []

    active_weights = weights or DEFAULT_WEIGHTS
    fused_scores: dict[UUID, float] = defaultdict(float)

    for stream_name, candidates in stream_results.items():
        weight = active_weights.get(stream_name, 1.0)
        for rank_idx, (item_id, _) in enumerate(candidates, start=1):
            rrf_component = weight * (1.0 / (k + rank_idx))
            fused_scores[item_id] += rrf_component

    # Sort candidates descending by fused score
    sorted_candidates = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return [(item_id, round(score, 6)) for item_id, score in sorted_candidates]


__all__ = [
    "DEFAULT_WEIGHTS",
    "merge_candidates_rrf",
]
