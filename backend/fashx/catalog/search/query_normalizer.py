from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from database.models.catalog_search import SearchSynonymRecord

# Punctuation regex keeping alphanumeric, spaces, and hyphens
PUNCT_RE = re.compile(r"[^\w\s\-]")
WHITESPACE_RE = re.compile(r"\s+")

# In-memory baseline fashion synonyms
STATIC_SYNONYMS: dict[str, str] = {
    "tee": "t-shirt",
    "tees": "t-shirts",
    "kurti": "short kurta",
    "kurtis": "kurtas",
    "denim": "jeans",
    "shrt": "shirt",
    "blak": "black",
    "trouser": "pants",
}


def normalize_query_text(query: str | None) -> str:
    """Normalize query text: strip punctuation, convert to lowercase, collapse whitespace."""
    if not query:
        return ""
    clean = PUNCT_RE.sub(" ", query.lower())
    clean = WHITESPACE_RE.sub(" ", clean).strip()
    return clean


def sanitize_query(query: str | None) -> str:
    """Sanitize query string against common injection patterns."""
    if not query:
        return ""
    # Strip dangerous SQL tokens
    return re.sub(r"['\";\-\-]", "", query).strip()


def expand_synonyms(tokens: list[str], session: Session | None = None) -> list[str]:
    """Expand tokens with synonyms from database registry or static dictionary."""
    expanded: list[str] = list(tokens)
    for tok in tokens:
        # Check static synonyms
        if tok in STATIC_SYNONYMS:
            syn = STATIC_SYNONYMS[tok]
            if syn not in expanded:
                expanded.append(syn)

        # Check DB synonyms if session available
        if session is not None:
            stmt = select(SearchSynonymRecord).where(
                or_(
                    SearchSynonymRecord.term == tok,
                    SearchSynonymRecord.synonym == tok,
                )
            )
            syn_records = session.scalars(stmt).all()
            for rec in syn_records:
                target = rec.synonym if rec.term == tok else rec.term
                if target not in expanded:
                    expanded.append(target)

    return expanded


__all__ = [
    "expand_synonyms",
    "normalize_query_text",
    "sanitize_query",
]
