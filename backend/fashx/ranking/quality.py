"""Product and merchant quality controls (Task 8.4.10)."""

from __future__ import annotations

from fashx.ranking.contracts import RankingCandidate


def product_quality_score(
    image_quality: float | None,
    attribute_completeness: float | None,
    data_freshness: float | None,
) -> float:
    """Compute normalized product quality score without inventing missing dimensions."""
    available = [
        value
        for value in (image_quality, attribute_completeness, data_freshness)
        if value is not None
    ]
    if not available:
        return 0.5
    return max(0.0, min(1.0, sum(available) / len(available)))


def merchant_quality_score(
    feed_reliability: float | None,
    merchant_freshness: float | None,
    broken_link_rate: float | None,
    *,
    is_new_merchant: bool = False,
) -> float:
    """Compute merchant operational quality with a cold-start neutral policy."""
    if is_new_merchant and feed_reliability is None and merchant_freshness is None:
        return 0.5

    dims: list[float] = []
    if feed_reliability is not None:
        dims.append(feed_reliability)
    if merchant_freshness is not None:
        dims.append(merchant_freshness)
    if broken_link_rate is not None:
        dims.append(max(0.0, min(1.0, 1.0 - broken_link_rate)))

    if not dims:
        return 0.5
    return max(0.0, min(1.0, sum(dims) / len(dims)))


def combined_quality_score(candidate: RankingCandidate) -> float:
    """Combine product and merchant quality; sponsored placement never inflates quality."""
    prod_q = product_quality_score(
        candidate.image_quality,
        candidate.attribute_completeness,
        candidate.data_freshness,
    )
    merch_q = merchant_quality_score(
        candidate.merchant_feed_reliability,
        candidate.merchant_freshness,
        candidate.merchant_broken_link_rate,
        is_new_merchant=candidate.is_new_merchant,
    )
    return max(0.0, min(1.0, 0.6 * prod_q + 0.4 * merch_q))
