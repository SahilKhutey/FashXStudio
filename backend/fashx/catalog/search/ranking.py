from __future__ import annotations

from uuid import UUID

from database.models.catalog_search import ProductSearchDocumentRecord


def apply_business_ranking(
    candidates: list[tuple[UUID, float]],
    query_text: str | None,
    search_docs: dict[UUID, ProductSearchDocumentRecord],
    brand_map: dict[UUID, str] | None = None,
) -> list[tuple[UUID, float]]:
    """Apply domain-specific boosts to merged candidate scores.

    Boosts:
    - Exact Title match (+25%)
    - Brand match in query (+20%)
    - Verified in-stock attributes (+15%)
    """
    if not candidates or not query_text:
        return candidates

    clean_q = query_text.lower().strip()
    brands = brand_map or {}
    boosted: list[tuple[UUID, float]] = []

    for item_id, base_score in candidates:
        score = base_score
        doc = search_docs.get(item_id)

        if doc is not None:
            # 1. Exact or Substring Title Match
            if clean_q == doc.title.lower():
                score *= 1.25
            elif clean_q in doc.title.lower():
                score *= 1.15

            # 2. Brand Match
            if doc.brand_id and doc.brand_id in brands:
                brand_name = brands[doc.brand_id].lower()
                if brand_name in clean_q:
                    score *= 1.20

            # 3. Verified High-Confidence Attributes
            attrs = doc.indexed_attributes_json or {}
            if attrs.get("confidence", 0.0) >= 0.95:
                score *= 1.10

        boosted.append((item_id, round(score, 6)))

    # Sort descending by score with stable tie-breaker on UUID string
    boosted.sort(key=lambda x: (x[1], str(x[0])), reverse=True)
    return boosted


__all__ = ["apply_business_ranking"]
