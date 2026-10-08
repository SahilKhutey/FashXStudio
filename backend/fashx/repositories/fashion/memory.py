from __future__ import annotations

from uuid import UUID

from fashx.core.errors import ConflictError
from fashx.domain.fashion.entities import (
    ProductFashionProfile,
    TaxonomyNode,
)
from fashx.domain.fashion.repository import (
    ProductFashionRepository,
    TaxonomyRepository,
)


class InMemoryTaxonomyRepository(TaxonomyRepository):

    def __init__(self) -> None:
        self._items: dict[UUID, TaxonomyNode] = {}

    async def get(
        self,
        node_id: UUID,
    ) -> TaxonomyNode | None:
        return self._items.get(node_id)

    async def get_by_slug(
        self,
        slug: str,
    ) -> TaxonomyNode | None:

        normalized = slug.strip().lower()

        for node in self._items.values():
            if node.slug.strip().lower() == normalized:
                return node

        return None

    async def save(
        self,
        node: TaxonomyNode,
    ) -> TaxonomyNode:

        existing = await self.get_by_slug(node.slug)

        if existing is not None and existing.id != node.id:
            raise ConflictError(
                "Taxonomy slug already exists.",
                {"slug": node.slug},
            )

        self._items[node.id] = node

        return node

    async def list_children(
        self,
        parent_id: UUID | None,
    ) -> list[TaxonomyNode]:

        return [
            node
            for node in self._items.values()
            if node.parent_id == parent_id
        ]

    async def list_all(self) -> list[TaxonomyNode]:
        return list(self._items.values())


class InMemoryProductFashionRepository(
    ProductFashionRepository
):

    def __init__(self) -> None:
        self._items: dict[UUID, ProductFashionProfile] = {}

    async def get_by_product(
        self,
        product_id: UUID,
    ) -> ProductFashionProfile | None:

        for profile in self._items.values():
            if profile.product_id == product_id:
                return profile

        return None

    async def save(
        self,
        profile: ProductFashionProfile,
    ) -> ProductFashionProfile:

        if profile.product_id is None:
            raise ValueError("Product ID is required.")

        existing = await self.get_by_product(
            profile.product_id
        )

        if existing is not None and existing.id != profile.id:
            del self._items[existing.id]

        self._items[profile.id] = profile

        return profile

    async def delete_by_product(
        self,
        product_id: UUID,
    ) -> None:

        existing = await self.get_by_product(product_id)

        if existing is not None:
            del self._items[existing.id]
