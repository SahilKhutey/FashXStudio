from .contracts import SearchRequest, SuggestionRequest
from .enums import SearchMode, SearchResultType, SortOption
from .matcher import match_score
from .models import SearchDocument, SearchResponse, SearchResult
from .repository import SearchRepository
from .tokenizer import tokenize


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self.repository = repository

    def search(self, request: SearchRequest) -> SearchResponse:
        self._validate(request)
        documents = self._filter(self._mode(list(self.repository.all()), request.mode), request)
        results = [
            SearchResult(document, self._score(request.query, document)) for document in documents
        ]
        results = self._sort(results, request.sort)
        start = (request.page - 1) * request.page_size
        return SearchResponse(
            request.query,
            tuple(results[start : start + request.page_size]),
            len(results),
            request.page,
            request.page_size,
        )

    def suggestions(self, request: SuggestionRequest) -> tuple[str, ...]:
        if not request.user_id.strip() or not 1 <= request.limit <= 20:
            raise ValueError("A user ID and a suggestion limit between 1 and 20 are required.")
        tokens = tokenize(request.query)
        if not tokens:
            return ()
        titles = [
            document.title
            for document in self.repository.all()
            if any(token in document.title.lower() for token in tokens)
        ]
        return tuple(dict.fromkeys(titles))[: request.limit]

    @staticmethod
    def _validate(request: SearchRequest) -> None:
        if (
            not request.user_id.strip()
            or not 1 <= request.page
            or not 1 <= request.page_size <= 100
        ):
            raise ValueError(
                "A user ID, positive page, and page size between 1 and 100 are required."
            )
        if request.filters.min_price is not None and request.filters.min_price < 0:
            raise ValueError("Minimum price cannot be negative.")
        if request.filters.max_price is not None and request.filters.max_price < 0:
            raise ValueError("Maximum price cannot be negative.")
        if (
            request.filters.min_price is not None
            and request.filters.max_price is not None
            and request.filters.min_price > request.filters.max_price
        ):
            raise ValueError("Minimum price cannot exceed maximum price.")

    @staticmethod
    def _mode(documents: list[SearchDocument], mode: SearchMode) -> list[SearchDocument]:
        mapping = {
            SearchMode.PRODUCTS: SearchResultType.PRODUCT,
            SearchMode.OUTFITS: SearchResultType.OUTFIT,
            SearchMode.CONTENT: SearchResultType.CONTENT,
            SearchMode.TRENDS: SearchResultType.TREND,
        }
        return (
            documents
            if mode == SearchMode.GLOBAL
            else [document for document in documents if document.result_type == mapping[mode]]
        )

    @staticmethod
    def _filter(documents: list[SearchDocument], request: SearchRequest) -> list[SearchDocument]:
        filters = request.filters
        return [
            document
            for document in documents
            if (not filters.category or document.category == filters.category)
            and (not filters.subcategory or document.subcategory == filters.subcategory)
            and (not filters.style or filters.style in document.styles)
            and (not filters.color or filters.color in document.colors)
            and (not filters.brand or document.brand == filters.brand)
            and (not filters.region or not document.regions or filters.region in document.regions)
            and (
                filters.min_price is None
                or document.price is not None
                and document.price >= filters.min_price
            )
            and (
                filters.max_price is None
                or document.price is not None
                and document.price <= filters.max_price
            )
        ]

    @staticmethod
    def _score(query: str, document: SearchDocument) -> float:
        return (
            0.6 * match_score(query, document)
            + 0.2 * document.relevance_score
            + 0.1 * document.trend_score
            + 0.1 * document.popularity_score
        )

    @staticmethod
    def _sort(results: list[SearchResult], option: SortOption) -> list[SearchResult]:
        keys = {
            SortOption.RELEVANCE: lambda result: result.score,
            SortOption.POPULARITY: lambda result: result.document.popularity_score,
            SortOption.TRENDING: lambda result: result.document.trend_score,
            SortOption.NEWEST: lambda result: result.document.created_at,
            SortOption.PRICE_LOW_TO_HIGH: lambda result: (
                result.document.price if result.document.price is not None else float("inf")
            ),
            SortOption.PRICE_HIGH_TO_LOW: lambda result: (
                result.document.price if result.document.price is not None else float("-inf")
            ),
        }
        return sorted(results, key=keys[option], reverse=option != SortOption.PRICE_LOW_TO_HIGH)
