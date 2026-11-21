from __future__ import annotations

from typing import Any


def generate_no_result_suggestions(
    applied_filters: dict[str, Any],
    query_text: str | None = None,
) -> list[str]:
    """Generate constructive suggestions for shoppers when zero items match a search request."""
    suggestions: list[str] = []

    if applied_filters.get("max_price") is not None:
        suggestions.append("Try relaxing or removing the price filter to see more items")

    if applied_filters.get("size") is not None:
        suggestions.append(f"Size '{applied_filters['size']}' is currently out of stock; try alternative sizes")

    if applied_filters.get("brand_id") is not None:
        suggestions.append("Try clearing the brand filter to explore similar styles from other brands")

    if applied_filters.get("category_id") is not None:
        suggestions.append("Try browsing a broader category to see more options")

    if applied_filters.get("color_id") is not None:
        suggestions.append("Try removing the color filter to view all color variants")

    if query_text and len(query_text.split()) > 3:
        suggestions.append("Try using fewer or more general keywords (e.g. 'cotton shirt' instead of long phrase)")

    if not suggestions:
        suggestions.append("Check spelling or try searching for broader fashion categories like 'kurtas', 'shirts', or 'dresses'")

    return suggestions


__all__ = ["generate_no_result_suggestions"]
