from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.catalog.search import CatalogItemSummary


class FeedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product: CatalogItemSummary
    reasons: list[str] = Field(default_factory=list, max_length=8)


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None


class FeedQuery(BaseModel):
    category: str | None = Field(default=None, max_length=64)
    subcategory: str | None = Field(default=None, max_length=64)
    price_min: int | None = Field(default=None, ge=0)
    price_max: int | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=50)
    cursor: str | None = None


class FeedExclusionRequest(BaseModel):
    product_id: UUID
