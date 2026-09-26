from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.fashion.enums import (
    ClassificationSource,
    TaxonomyType,
)


class TaxonomyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)

    taxonomy_type: TaxonomyType

    parent_id: UUID | None = None

    description: str | None = None

    metadata: dict[str, str] = Field(
        default_factory=dict
    )


class FashionAttributeRequest(BaseModel):
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class ProductFashionClassificationRequest(BaseModel):
    taxonomy_node_ids: set[UUID] = Field(
        default_factory=set
    )

    attributes: list[FashionAttributeRequest] = Field(
        default_factory=list
    )

    source: ClassificationSource = (
        ClassificationSource.MANUAL
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class TaxonomyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    taxonomy_type: TaxonomyType
    parent_id: UUID | None
    description: str | None


class FashionClassificationResponse(BaseModel):
    id: UUID
    product_id: UUID | None
    taxonomy_node_ids: set[UUID]
    source: ClassificationSource
    confidence: float | None
    version: int
