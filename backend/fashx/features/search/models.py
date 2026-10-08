from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .enums import SearchResultType


@dataclass(frozen=True)
class SearchDocument:
    document_id: str
    result_type: SearchResultType
    title: str
    description: str = ""
    category: str | None = None
    subcategory: str | None = None
    tags: tuple[str, ...] = ()
    styles: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    brand: str | None = None
    price: float | None = None
    popularity_score: float = 0.0
    trend_score: float = 0.0
    relevance_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    document: SearchDocument
    score: float


@dataclass(frozen=True)
class SearchResponse:
    query: str
    results: tuple[SearchResult, ...]
    total: int
    page: int
    page_size: int
