from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from fashx.domain.fashion.entities import (
    FashionAttribute,
    TaxonomyNode,
)
from fashx.domain.fashion.service import FashionService

from .fashion_schemas import (
    FashionClassificationResponse,
    ProductFashionClassificationRequest,
    TaxonomyCreateRequest,
    TaxonomyResponse,
)

router = APIRouter(
    prefix="/fashion",
    tags=["fashion"],
)


def get_fashion_service() -> FashionService:
    register_core_services()
    return get_core_runtime().registry.get(
        "fashion_service"
    )


@router.post(
    "/taxonomy",
    response_model=TaxonomyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_taxonomy(
    payload: TaxonomyCreateRequest,
    service: FashionService = Depends(
        get_fashion_service
    ),
):
    node = TaxonomyNode(
        name=payload.name,
        slug=payload.slug,
        taxonomy_type=payload.taxonomy_type,
        parent_id=payload.parent_id,
        description=payload.description,
        metadata=payload.metadata,
    )

    return await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=node,
    )


@router.get(
    "/taxonomy",
    response_model=list[TaxonomyResponse],
)
async def list_taxonomy_children(
    parent_id: UUID | None = Query(default=None),
    service: FashionService = Depends(
        get_fashion_service
    ),
):
    return await service.list_children(parent_id)


@router.get(
    "/taxonomy/{node_id}",
    response_model=TaxonomyResponse,
)
async def get_taxonomy(
    node_id: UUID,
    service: FashionService = Depends(
        get_fashion_service
    ),
):
    return await service.get_taxonomy_node(node_id)


@router.put(
    "/products/{product_id}/classification",
    response_model=FashionClassificationResponse,
)
async def classify_product(
    product_id: UUID,
    payload: ProductFashionClassificationRequest,
    service: FashionService = Depends(
        get_fashion_service
    ),
):
    attributes = [
        FashionAttribute(
            key=item.key,
            value=item.value,
        )
        for item in payload.attributes
    ]

    return await service.classify_product(
        context=CoreContext.create(),
        product_id=product_id,
        taxonomy_node_ids=payload.taxonomy_node_ids,
        attributes=attributes,
        source=payload.source,
        confidence=payload.confidence,
    )


@router.get(
    "/products/{product_id}/classification",
    response_model=FashionClassificationResponse,
)
async def get_product_classification(
    product_id: UUID,
    service: FashionService = Depends(
        get_fashion_service
    ),
):
    return await service.get_product_classification(
        product_id
    )
