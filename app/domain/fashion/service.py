from __future__ import annotations

from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus

from .classification import validate_parent
from .entities import (
    FashionAttribute,
    ProductFashionProfile,
    TaxonomyNode,
)
from .enums import ClassificationSource
from .events import (
    ProductFashionClassificationChanged,
    TaxonomyNodeCreated,
)
from .repository import (
    ProductFashionRepository,
    TaxonomyRepository,
)


class FashionService:

    def __init__(
        self,
        taxonomy_repository: TaxonomyRepository,
        classification_repository: ProductFashionRepository,
        event_bus: EventBus,
    ) -> None:
        self.taxonomy_repository = taxonomy_repository
        self.classification_repository = (
            classification_repository
        )
        self.event_bus = event_bus

    async def create_taxonomy_node(
        self,
        *,
        context: CoreContext,
        node: TaxonomyNode,
    ) -> TaxonomyNode:

        validate_parent(node)
        node.validate()

        if node.parent_id is not None:
            parent = await self.taxonomy_repository.get(
                node.parent_id
            )

            if parent is None:
                raise NotFoundError(
                    "Taxonomy parent does not exist.",
                    {
                        "parent_id": str(node.parent_id)
                    },
                )

        await self.taxonomy_repository.save(node)

        await self.event_bus.publish(
            TaxonomyNodeCreated(
                entity_id=node.id,
                correlation_id=context.correlation_id,
            )
        )

        return node

    async def get_taxonomy_node(
        self,
        node_id: UUID,
    ) -> TaxonomyNode:

        node = await self.taxonomy_repository.get(node_id)

        if node is None:
            raise NotFoundError(
                "Taxonomy node was not found.",
                {"node_id": str(node_id)},
            )

        return node

    async def list_children(
        self,
        parent_id: UUID | None,
    ) -> list[TaxonomyNode]:

        return await self.taxonomy_repository.list_children(
            parent_id
        )

    async def classify_product(
        self,
        *,
        context: CoreContext,
        product_id: UUID,
        taxonomy_node_ids: set[UUID],
        attributes: list[FashionAttribute],
        source: ClassificationSource,
        confidence: float | None = None,
    ) -> ProductFashionProfile:

        for node_id in taxonomy_node_ids:
            node = await self.taxonomy_repository.get(node_id)

            if node is None:
                raise NotFoundError(
                    "Fashion taxonomy node was not found.",
                    {"node_id": str(node_id)},
                )

        profile = (
            await self.classification_repository
            .get_by_product(product_id)
        )

        if profile is None:
            profile = ProductFashionProfile(
                product_id=product_id,
            )

        profile.taxonomy_node_ids = set(
            taxonomy_node_ids
        )
        profile.attributes = list(attributes)
        profile.source = source
        profile.confidence = confidence

        profile.validate()

        if profile.version > 1:
            profile.touch()

        await self.classification_repository.save(
            profile
        )

        await self.event_bus.publish(
            ProductFashionClassificationChanged(
                entity_id=product_id,
                correlation_id=context.correlation_id,
            )
        )

        return profile

    async def get_product_classification(
        self,
        product_id: UUID,
    ) -> ProductFashionProfile:

        profile = (
            await self.classification_repository
            .get_by_product(product_id)
        )

        if profile is None:
            raise NotFoundError(
                "Product fashion classification was not found.",
                {"product_id": str(product_id)},
            )

        return profile
