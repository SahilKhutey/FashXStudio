import pytest

from api.app.features.search.contracts import SearchFilters, SearchRequest, SuggestionRequest
from api.app.features.search.enums import SearchMode, SearchResultType, SearchStatus, SortOption
from api.app.features.search.matcher import match_score
from api.app.features.search.models import SearchDocument
from api.app.features.search.repository import SearchRepository
from api.app.features.search.service import SearchService
from api.app.features.search.state import SearchState
from api.app.features.search.tokenizer import tokenize


def service() -> SearchService:
    return SearchService(
        SearchRepository(
            (
                SearchDocument(
                    "black",
                    SearchResultType.PRODUCT,
                    "Black Casual Shirt",
                    category="shirts",
                    colors=("black",),
                    price=30,
                    relevance_score=0.9,
                ),
                SearchDocument(
                    "blue",
                    SearchResultType.PRODUCT,
                    "Blue Jeans",
                    category="jeans",
                    colors=("blue",),
                    price=50,
                    popularity_score=0.9,
                ),
                SearchDocument(
                    "trend", SearchResultType.TREND, "Monochrome Trend", trend_score=1.0
                ),
            )
        )
    )


def test_tokenizer_match_suggestions_and_mode() -> None:
    assert tokenize("The Black Casual Shirt") == ("black", "casual", "shirt")
    assert match_score("black shirt", service().repository.all()[0]) == 1.0
    assert service().suggestions(SuggestionRequest("user", "black")) == ("Black Casual Shirt",)
    assert service().search(SearchRequest("user", mode=SearchMode.TRENDS)).total == 1


def test_search_filters_sorts_paginates_and_tracks_ui_states() -> None:
    result = service().search(
        SearchRequest(
            "user",
            filters=SearchFilters(category="shirts", color="black"),
            sort=SortOption.PRICE_LOW_TO_HIGH,
            page_size=1,
        )
    )
    assert result.total == 1 and result.results[0].document.document_id == "black"
    with pytest.raises(ValueError):
        service().search(SearchRequest("", page=0))
    state = SearchState()
    state.searching("shirt")
    state.success(False)
    assert state.status == SearchStatus.EMPTY
    state.failure("Unavailable")
    assert state.status == SearchStatus.ERROR
