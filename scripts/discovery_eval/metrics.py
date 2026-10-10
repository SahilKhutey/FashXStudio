"""Discovery ranking evaluation metrics (nDCG@k, Precision@k, distinct count, max share)."""

import math
from collections import Counter
from collections.abc import Callable
from typing import Any


def dcg(rels: list[int | float]) -> float:
    """Discounted Cumulative Gain with exponential gain formula."""
    return sum((2.0**r - 1.0) / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked: list[str], judgments: dict[str, int | float], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain at rank k."""
    rels = [judgments.get(g, 0.0) for g in ranked[:k]]
    # Ideal ranking is the highest judged scores sorted descending
    ideal = sorted(judgments.values(), reverse=True)[:k]
    d = dcg(ideal)
    if d <= 0.0:
        return 0.0
    return dcg(rels) / d


def precision_at_k(ranked: list[str], judgments: dict[str, int | float], k: int = 10, rel_min: int | float = 2) -> float:
    """Fraction of top-k items with relevance score >= rel_min."""
    top = ranked[:k]
    if not top:
        return 0.0
    return sum(judgments.get(g, 0.0) >= rel_min for g in top) / len(top)


def distinct[T](items: list[T], key: Callable[[T], Any], k: int = 20) -> int:
    """Count of distinct key values across top-k items."""
    return len({key(i) for i in items[:k]})


def max_share[T](items: list[T], key: Callable[[T], Any], k: int = 20) -> float:
    """Maximum proportion of any single key value across top-k items."""
    top = items[:k]
    if not top:
        return 0.0
    c = Counter(key(i) for i in top)
    total = sum(c.values())
    return max(c.values()) / max(total, 1) if total > 0 else 0.0
