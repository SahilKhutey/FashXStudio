"""Information retrieval and safety metrics for ranking evaluation (Task 8.4.14)."""

from __future__ import annotations

import math


def dcg_at_k(relevances: list[int], k: int) -> float:
    """Discounted Cumulative Gain at cutoff K."""
    if k <= 0:
        return 0.0
    score = 0.0
    for index, relevance in enumerate(relevances[:k]):
        score += (2**relevance - 1) / math.log2(index + 2)
    return score


def ndcg_at_k(
    ranked_relevances: list[int],
    ideal_relevances: list[int],
    k: int,
) -> float:
    """Normalized Discounted Cumulative Gain at cutoff K."""
    actual = dcg_at_k(ranked_relevances, k)
    ideal = dcg_at_k(sorted(ideal_relevances, reverse=True), k)
    if ideal == 0.0:
        return 0.0
    return actual / ideal


def precision_at_k(
    ranked_relevances: list[int],
    k: int,
    relevance_threshold: int = 2,
) -> float:
    """Fraction of top-K ranked results meeting the relevance threshold."""
    results = ranked_relevances[:k]
    if not results:
        return 0.0
    relevant = sum(value >= relevance_threshold for value in results)
    return relevant / len(results)


def recall_at_k(
    ranked_relevances: list[int],
    total_relevant: int,
    k: int,
    relevance_threshold: int = 2,
) -> float:
    """Fraction of all relevant items retrieved in top-K."""
    if total_relevant <= 0:
        return 0.0
    retrieved_relevant = sum(value >= relevance_threshold for value in ranked_relevances[:k])
    return min(1.0, retrieved_relevant / total_relevant)


def reciprocal_rank(
    ranked_relevances: list[int],
    relevance_threshold: int = 2,
) -> float:
    """Reciprocal rank of the first relevant item (0.0 if none)."""
    for index, relevance in enumerate(ranked_relevances):
        if relevance >= relevance_threshold:
            return 1.0 / (index + 1)
    return 0.0
