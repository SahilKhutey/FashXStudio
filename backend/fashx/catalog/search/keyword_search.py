from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import Brand, MerchantProduct
from database.models.catalog_search import ProductSearchDocumentRecord
from fashx.catalog.search.query_normalizer import expand_synonyms, normalize_query_text

logger = logging.getLogger(__name__)


def execute_keyword_search(
    session: Session,
    query_text: str | None,
    limit: int = 50,
) -> list[tuple[UUID, float]]:
    """Execute full-text keyword retrieval across title, brand, and approved attributes.

    Returns:
        List of (merchant_product_id, relevance_score) sorted descending by score.
    """
    if not query_text:
        return []

    normalized = normalize_query_text(query_text)
    tokens = [t for t in normalized.split() if t]
    if not tokens:
        return []

    expanded_tokens = expand_synonyms(tokens, session)

    # 1. Query search documents
    stmt = (
        select(ProductSearchDocumentRecord, Brand.name)
        .outerjoin(Brand, ProductSearchDocumentRecord.brand_id == Brand.id)
    )
    docs = session.execute(stmt).all()

    scored_candidates: list[tuple[UUID, float]] = []

    for doc_rec, brand_name in docs:
        score = 0.0
        title_lower = (doc_rec.title or "").lower()
        desc_lower = (doc_rec.description or "").lower()
        search_doc_lower = (doc_rec.search_document or "").lower()
        brand_lower = (brand_name or "").lower()
        attrs = doc_rec.indexed_attributes_json or {}
        garment_type = str(attrs.get("garment_type", "")).lower()
        color = str(attrs.get("color", "")).lower()
        occasion = str(attrs.get("occasion", "")).lower()

        # Exact phrase match in title or search document
        if normalized in title_lower:
            score += 2.0
        elif normalized in search_doc_lower:
            score += 1.5

        for tok in expanded_tokens:
            tok_lower = tok.lower()
            if tok_lower in title_lower:
                score += 1.0  # Weight A (Title)
            if brand_lower and tok_lower in brand_lower:
                score += 1.0  # Weight A (Brand)
            if search_doc_lower and tok_lower in search_doc_lower:
                score += 0.8  # Weight B (Search Document)
            if garment_type and tok_lower in garment_type:
                score += 0.6  # Weight B (Garment Type)
            if color and tok_lower in color:
                score += 0.5  # Weight B (Color)
            if occasion and tok_lower in occasion:
                score += 0.4  # Weight B (Occasion)
            if desc_lower and tok_lower in desc_lower:
                score += 0.1  # Weight D (Description)

        if score > 0.0:
            scored_candidates.append((doc_rec.merchant_product_id, round(score, 4)))

    # Fallback to direct merchant_products if search documents are not yet populated
    if not scored_candidates:
        mp_stmt = select(MerchantProduct).where(MerchantProduct.status == "active")
        mps = session.scalars(mp_stmt).all()
        for mp in mps:
            score = 0.0
            t_lower = (mp.title or "").lower()
            d_lower = (mp.description or "").lower()
            if normalized in t_lower:
                score += 2.0
            for tok in expanded_tokens:
                tok_lower = tok.lower()
                if tok_lower in t_lower:
                    score += 1.0
                elif tok_lower in d_lower:
                    score += 0.1
            if score > 0.0:
                scored_candidates.append((mp.id, round(score, 4)))

    # Sort descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return scored_candidates[:limit]


__all__ = ["execute_keyword_search"]
