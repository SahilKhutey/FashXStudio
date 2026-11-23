from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from fashx.catalog.search.query_normalizer import normalize_query_text

PRICE_UNDER_RE = re.compile(r"\b(?:under|below|less\s+than)\s+(?:rs\.?|inr|₹)?\s*(\d+)\b", re.IGNORECASE)
PRICE_RANGE_RE = re.compile(r"\b(?:rs\.?|inr|₹)?\s*(\d+)\s*(?:to|-)\s*(?:rs\.?|inr|₹)?\s*(\d+)\b", re.IGNORECASE)
SIZE_RE = re.compile(r"\bsize\s+([a-zA-Z0-9]+)\b", re.IGNORECASE)

KNOWN_COLORS = {
    "black", "white", "navy blue", "navy", "blue", "red", "green", "yellow",
    "maroon", "beige", "brown", "pink", "grey", "gray", "olive", "multicolor",
}

KNOWN_OCCASIONS = {
    "casual", "formal", "office", "party", "festive", "wedding", "traditional", "sports",
}


@dataclass(frozen=True)
class ParsedSearchQuery:
    """Interpreted search query terms and inferred query filters."""

    raw_query: str
    clean_query: str
    tokens: list[str] = field(default_factory=list)
    inferred_min_price: Decimal | None = None
    inferred_max_price: Decimal | None = None
    inferred_size: str | None = None
    inferred_color: str | None = None
    inferred_occasion: str | None = None


def parse_query(raw_query: str | None) -> ParsedSearchQuery:
    """Parse raw query string into keyword tokens and optional inferred attribute filters."""
    if not raw_query:
        return ParsedSearchQuery(raw_query="", clean_query="", tokens=[])

    text = raw_query.strip()
    inferred_min_p: Decimal | None = None
    inferred_max_p: Decimal | None = None
    inferred_sz: str | None = None
    inferred_col: str | None = None
    inferred_occ: str | None = None

    # 1. Price extraction
    range_match = PRICE_RANGE_RE.search(text)
    if range_match:
        p1 = Decimal(range_match.group(1))
        p2 = Decimal(range_match.group(2))
        inferred_min_p = min(p1, p2)
        inferred_max_p = max(p1, p2)
        text = PRICE_RANGE_RE.sub(" ", text)
    else:
        under_match = PRICE_UNDER_RE.search(text)
        if under_match:
            inferred_max_p = Decimal(under_match.group(1))
            text = PRICE_UNDER_RE.sub(" ", text)

    # 2. Size extraction
    size_match = SIZE_RE.search(text)
    if size_match:
        inferred_sz = size_match.group(1).upper()
        text = SIZE_RE.sub(" ", text)

    # 3. Clean and tokenize remaining text
    normalized = normalize_query_text(text)
    tokens = [t for t in normalized.split() if t]

    # 4. Check for known colors
    for col in KNOWN_COLORS:
        if col in normalized:
            inferred_col = col
            break

    # 5. Check for known occasions
    for occ in KNOWN_OCCASIONS:
        if occ in tokens:
            inferred_occ = occ
            break

    return ParsedSearchQuery(
        raw_query=raw_query,
        clean_query=normalized,
        tokens=tokens,
        inferred_min_price=inferred_min_p,
        inferred_max_price=inferred_max_p,
        inferred_size=inferred_sz,
        inferred_color=inferred_col,
        inferred_occasion=inferred_occ,
    )


__all__ = [
    "ParsedSearchQuery",
    "parse_query",
]
