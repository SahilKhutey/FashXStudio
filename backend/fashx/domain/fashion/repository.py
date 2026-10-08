from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import ProductFashionProfile, TaxonomyNode


class TaxonomyRepository(ABC):

    @abstractmethod
    async def get(
        self,
        node_id: UUID,
    ) -> TaxonomyNode | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
    ) -> TaxonomyNode | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        node: TaxonomyNode,
    ) -> TaxonomyNode:
        raise NotImplementedError

    @abstractmethod
    async def list_children(
        self,
        parent_id: UUID | None,
    ) -> list[TaxonomyNode]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
    ) -> list[TaxonomyNode]:
        raise NotImplementedError


class ProductFashionRepository(ABC):

    @abstractmethod
    async def get_by_product(
        self,
        product_id: UUID,
    ) -> ProductFashionProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        profile: ProductFashionProfile,
    ) -> ProductFashionProfile:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_product(
        self,
        product_id: UUID,
    ) -> None:
        raise NotImplementedError
