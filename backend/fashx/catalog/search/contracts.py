from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ProductSearchRequest(BaseModel):
    """Unified shopper search request contract."""

    q: str | None = Field(default=None, max_length=200, description="Shopper search query text")
    category_id: UUID | None = Field(default=None, description="Phase 06.1 taxonomy category UUID")
    brand_id: UUID | None = Field(default=None, description="Canonical brand entity UUID")
    color_id: UUID | None = Field(default=None, description="Normalized taxonomy color UUID")
    occasion_id: UUID | None = Field(default=None, description="Enriched occasion UUID")
    size: str | None = Field(default=None, max_length=40, description="Size label (e.g. 'M', '38')")
    min_price: Decimal | None = Field(default=None, ge=0, description="Minimum price filter (>= 0)")
    max_price: Decimal | None = Field(default=None, ge=0, description="Maximum price filter (>= 0)")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="ISO currency code")
    in_stock: bool | None = Field(default=None, description="Require variant/offer to be in-stock")
    sort: Literal[
        "relevance",
        "price_low",
        "price_high",
        "newest",
        "recently_updated",
        "popularity",
        "similarity",
    ] = Field(default="relevance", description="Sorting criteria")
    limit: int = Field(default=20, ge=1, le=50, description="Result page size (1..50)")
    cursor: str | None = Field(default=None, max_length=2048, description="Opaque pagination cursor")

    @model_validator(mode="after")
    def validate_price_bounds(self) -> ProductSearchRequest:
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError(
                    f"min_price ({self.min_price}) cannot be greater than max_price ({self.max_price})"
                )
        return self


class SemanticSearchRequest(BaseModel):
    """Natural language semantic search request."""

    query: str = Field(..., min_length=1, max_length=500, description="Natural language search prompt")
    filters: dict[str, Any] = Field(default_factory=dict, description="Structured filter constraints")
    limit: int = Field(default=20, ge=1, le=50, description="Result page size")


class VisualSearchRequest(BaseModel):
    """Image-based visual similarity search request."""

    query_image_asset_id: UUID = Field(..., description="UUID of reference image asset")
    filters: dict[str, Any] = Field(default_factory=dict, description="Structured filter constraints")
    limit: int = Field(default=20, ge=1, le=50, description="Result page size")


class SearchInteractionEventRequest(BaseModel):
    """Interaction tracking payload."""

    session_id: UUID | None = None
    event_type: str = Field(..., description="Event type identifier (e.g. SEARCH_RESULT_CLICKED)")
    query: str | None = None
    filter_key: str | None = None
    filter_value: str | None = None
    product_id: UUID | None = None
    merchant_product_id: UUID | None = None
    rank_position: int | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SearchBrandInfo(BaseModel):
    id: UUID | None = None
    name: str


class SearchPriceInfo(BaseModel):
    amount: Decimal
    currency: str


class ProductSearchResultItem(BaseModel):
    product_id: UUID
    merchant_product_id: UUID
    title: str
    brand: SearchBrandInfo
    price: SearchPriceInfo
    availability: str
    matched_attributes: list[str] = Field(default_factory=list)
    primary_image_url: str | None = None
    similarity_score: float | None = None


class ProductSearchResponse(BaseModel):
    search_id: UUID
    query: str | None = None
    items: list[ProductSearchResultItem] = Field(default_factory=list)
    total: int = 0
    next_cursor: str | None = None
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    facets: dict[str, Any] = Field(default_factory=dict)
    sort: str = "relevance"


class SearchSuggestionsResponse(BaseModel):
    prefix: str
    suggestions: list[str] = Field(default_factory=list)


class SearchFacetsResponse(BaseModel):
    facets: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class SearchSessionResponse(BaseModel):
    session_id: UUID
    query: str | None = None
    total_results: int = 0
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    items: list[ProductSearchResultItem] = Field(default_factory=list)
    next_cursor: str | None = None


__all__ = [
    "ProductSearchRequest",
    "ProductSearchResponse",
    "ProductSearchResultItem",
    "SearchBrandInfo",
    "SearchFacetsResponse",
    "SearchInteractionEventRequest",
    "SearchPriceInfo",
    "SearchSessionResponse",
    "SearchSuggestionsResponse",
    "SemanticSearchRequest",
    "VisualSearchRequest",
]
