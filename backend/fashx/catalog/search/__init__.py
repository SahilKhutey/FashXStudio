from __future__ import annotations

from fashx.catalog.search.availability import filter_availability_and_takedowns
from fashx.catalog.search.candidate_merger import merge_candidates_rrf
from fashx.catalog.search.contracts import (
    ProductSearchRequest,
    ProductSearchResponse,
    ProductSearchResultItem,
    SearchBrandInfo,
    SearchFacetsResponse,
    SearchInteractionEventRequest,
    SearchPriceInfo,
    SearchSessionResponse,
    SearchSuggestionsResponse,
    SemanticSearchRequest,
    VisualSearchRequest,
)
from fashx.catalog.search.evaluation import (
    QueryJudgment,
    RelevanceMetrics,
    SearchRelevanceEvaluator,
)
from fashx.catalog.search.facets import compute_facets
from fashx.catalog.search.filters import apply_structured_filters
from fashx.catalog.search.keyword_search import execute_keyword_search
from fashx.catalog.search.no_results import generate_no_result_suggestions
from fashx.catalog.search.pagination import (
    InvalidCursorError,
    decode_cursor_token,
    generate_cursor_token,
)
from fashx.catalog.search.query_normalizer import (
    expand_synonyms,
    normalize_query_text,
    sanitize_query,
)
from fashx.catalog.search.query_parser import ParsedSearchQuery, parse_query
from fashx.catalog.search.ranking import apply_business_ranking
from fashx.catalog.search.router import router
from fashx.catalog.search.search_service import FashionSearchService
from fashx.catalog.search.semantic_search import execute_semantic_search
from fashx.catalog.search.size_filter import (
    apply_size_and_availability_filter,
    normalize_size_token,
)
from fashx.catalog.search.sorting import sort_search_results
from fashx.catalog.search.suggestions import get_query_suggestions
from fashx.catalog.search.visual_search import execute_visual_search

__all__ = [
    "FashionSearchService",
    "InvalidCursorError",
    "ParsedSearchQuery",
    "ProductSearchRequest",
    "ProductSearchResponse",
    "ProductSearchResultItem",
    "QueryJudgment",
    "RelevanceMetrics",
    "SearchBrandInfo",
    "SearchEvaluationRunRecord",
    "SearchFacetsResponse",
    "SearchInteractionEventRequest",
    "SearchPriceInfo",
    "SearchRelevanceEvaluator",
    "SearchSessionResponse",
    "SearchSuggestionsResponse",
    "SemanticSearchRequest",
    "VisualSearchRequest",
    "apply_business_ranking",
    "apply_size_and_availability_filter",
    "apply_structured_filters",
    "compute_facets",
    "decode_cursor_token",
    "execute_keyword_search",
    "execute_semantic_search",
    "execute_visual_search",
    "expand_synonyms",
    "filter_availability_and_takedowns",
    "generate_cursor_token",
    "generate_no_result_suggestions",
    "get_query_suggestions",
    "merge_candidates_rrf",
    "normalize_query_text",
    "normalize_size_token",
    "parse_query",
    "router",
    "sanitize_query",
    "sort_search_results",
]
