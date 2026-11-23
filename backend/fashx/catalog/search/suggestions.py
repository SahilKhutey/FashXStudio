from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog import Brand
from database.models.catalog_search import ProductSearchDocumentRecord, SearchSynonymRecord


def get_query_suggestions(
    session: Session,
    prefix: str,
    limit: int = 5,
) -> list[str]:
    """Retrieve auto-complete query suggestions based on brands, titles, and synonyms."""
    if not prefix or len(prefix.strip()) < 2:
        return []

    clean = prefix.strip().lower()
    suggestions: list[str] = []

    # 1. Matching brands
    brand_stmt = select(Brand.name).where(Brand.name.ilike(f"{clean}%")).limit(limit)
    brands = session.scalars(brand_stmt).all()
    suggestions.extend(brands)

    # 2. Matching search documents / titles
    if len(suggestions) < limit:
        doc_stmt = (
            select(ProductSearchDocumentRecord.title)
            .where(ProductSearchDocumentRecord.title.ilike(f"%{clean}%"))
            .limit(limit - len(suggestions))
        )
        titles = session.scalars(doc_stmt).all()
        for t in titles:
            if t not in suggestions:
                suggestions.append(t)

    # 3. Matching synonyms
    if len(suggestions) < limit:
        syn_stmt = (
            select(SearchSynonymRecord.synonym)
            .where(SearchSynonymRecord.term.ilike(f"{clean}%"))
            .limit(limit - len(suggestions))
        )
        syns = session.scalars(syn_stmt).all()
        for s in syns:
            if s not in suggestions:
                suggestions.append(s)

    return suggestions[:limit]


__all__ = ["get_query_suggestions"]
