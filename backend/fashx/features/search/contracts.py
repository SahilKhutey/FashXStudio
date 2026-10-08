from dataclasses import dataclass, field

from .enums import SearchMode, SortOption


@dataclass(frozen=True)
class SearchFilters:
    category: str | None = None
    subcategory: str | None = None
    style: str | None = None
    color: str | None = None
    brand: str | None = None
    region: str | None = None
    min_price: float | None = None
    max_price: float | None = None


@dataclass(frozen=True)
class SearchRequest:
    user_id: str
    query: str = ""
    mode: SearchMode = SearchMode.GLOBAL
    filters: SearchFilters = field(default_factory=SearchFilters)
    sort: SortOption = SortOption.RELEVANCE
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class SuggestionRequest:
    user_id: str
    query: str
    limit: int = 8
