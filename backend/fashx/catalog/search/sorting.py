from __future__ import annotations

from fashx.catalog.search.contracts import ProductSearchResultItem

ALLOWED_SORT_MODES = {
    "relevance",
    "price_low",
    "price_high",
    "newest",
    "recently_updated",
    "popularity",
    "similarity",
}


def sort_search_results(
    items: list[ProductSearchResultItem],
    sort_mode: str = "relevance",
) -> list[ProductSearchResultItem]:
    """Sort search result items by an allowed criteria with stable tie-breaking."""
    if sort_mode not in ALLOWED_SORT_MODES:
        raise ValueError(
            f"Invalid sort mode '{sort_mode}'. Must be one of {ALLOWED_SORT_MODES}"
        )

    if sort_mode == "relevance":
        # Keep incoming ranked order
        return items

    if sort_mode == "price_low":
        return sorted(items, key=lambda x: (x.price.amount, str(x.merchant_product_id)))

    if sort_mode == "price_high":
        return sorted(items, key=lambda x: (-x.price.amount, str(x.merchant_product_id)))

    if sort_mode == "similarity":
        return sorted(
            items,
            key=lambda x: (-(x.similarity_score or 0.0), str(x.merchant_product_id)),
        )

    # newest / recently_updated / popularity fallback
    return items


__all__ = [
    "ALLOWED_SORT_MODES",
    "sort_search_results",
]
