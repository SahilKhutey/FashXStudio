"""RC10 recommendation ranking evaluation metrics (nDCG@k, Precision@k, Recall@k)."""
from __future__ import annotations

from collections.abc import Sequence
from math import log2


def dcg_at_k(relevances: Sequence[float], k: int) -> float:
    """Calculates discounted cumulative gain at rank k."""
    if k <= 0:
        raise ValueError("k must be positive")
    score = 0.0
    for index, relevance in enumerate(relevances[:k]):
        if relevance < 0:
            raise ValueError("Relevance must be non-negative")
        score += float(relevance) / log2(index + 2)
    return score


def ndcg_at_k(
    ranked_relevances: Sequence[float],
    ideal_relevances: Sequence[float],
    k: int = 10,
) -> float:
    """Calculates normalized discounted cumulative gain at rank k."""
    if k <= 0:
        raise ValueError("k must be positive")
    ideal = dcg_at_k(
        sorted(ideal_relevances, reverse=True),
        k,
    )
    if ideal == 0.0:
        return 0.0
    return dcg_at_k(ranked_relevances, k) / ideal


def precision_at_k(relevances: Sequence[bool | float], k: int) -> float:
    """Calculates fraction of relevant items within top-k recommendations."""
    if k <= 0:
        raise ValueError("k must be positive")
    top = relevances[:k]
    if not top:
        return 0.0
    hits = sum(1.0 for r in top if r)
    return hits / float(k)


def recall_at_k(
    relevances: Sequence[bool | float],
    k: int,
    total_relevant: int,
) -> float:
    """Calculates fraction of total relevant items retrieved within top-k."""
    if k <= 0:
        raise ValueError("k must be positive")
    if total_relevant <= 0:
        raise ValueError("total_relevant must be positive")
    top = relevances[:k]
    hits = sum(1.0 for r in top if r)
    return hits / float(total_relevant)
