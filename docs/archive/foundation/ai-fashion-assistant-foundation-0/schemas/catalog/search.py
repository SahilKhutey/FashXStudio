from uuid import UUID

from pydantic import BaseModel, Field


class CatalogSearchParams(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    price_min: int | None = Field(default=None, ge=0)
    price_max: int | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    cursor: UUID | None = None


class CatalogItemSummary(BaseModel):
    id: UUID
    category: str
    subcategory: str | None = None
    brand_id: UUID | None = None
    version: int


class CatalogSearchResponse(BaseModel):
    products: list[CatalogItemSummary]
    next_cursor: str | None = None
