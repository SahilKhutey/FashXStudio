from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    customer_id: UUID | None = None
    region: str | None = None
    currency: str = "INR"
    category: str | None = None
    brand: str | None = None
    style: str | None = None
    color: str | None = None
    material: str | None = None
    occasion: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )
    exclude_product_ids: list[UUID] = Field(default_factory=list)


class RecommendationExplanationResponse(BaseModel):
    reason: str
    score: Decimal
    message: str


class RecommendationItemResponse(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    score: Decimal
    rank: int
    explanations: list[RecommendationExplanationResponse] = Field(
        default_factory=list
    )


class RecommendationResponse(BaseModel):
    items: list[RecommendationItemResponse]
    total_candidates: int
    engine_version: str
