"""Category relevance scoring backed by Phase 06 TaxonomyRegistry (Task 8.4.2)."""

from __future__ import annotations

from typing import Protocol

from fashx.catalog.taxonomy.registry import TaxonomyRegistry

CATEGORY_RELEVANCE: dict[str, float] = {
    "EXACT": 1.00,
    "RELATED": 0.65,
    "BROAD": 0.35,
    "UNRELATED": 0.00,
}


class TaxonomyInterface(Protocol):
    """Minimal taxonomy query contract consumed by category ranking."""

    @property
    def version(self) -> str: ...

    def is_related(self, requested_category_id: str, product_category_id: str) -> bool: ...

    def is_in_same_broad_category(
        self, requested_category_id: str, product_category_id: str
    ) -> bool: ...


class RegistryTaxonomyAdapter:
    """Adapter wrapping the Phase 06 TaxonomyRegistry for Phase 08.4."""

    def __init__(self, registry: TaxonomyRegistry) -> None:
        self._registry = registry

    @property
    def version(self) -> str:
        return self._registry.version

    def is_related(self, requested_category_id: str, product_category_id: str) -> bool:
        req = self._registry.get_category(requested_category_id)
        prod = self._registry.get_category(product_category_id)
        if req is None or prod is None:
            return False
        req_path = self._registry.get_category_path(requested_category_id)
        prod_path = self._registry.get_category_path(product_category_id)
        if requested_category_id in prod_path or product_category_id in req_path:
            return True
        return req.parent_id is not None and req.parent_id == prod.parent_id

    def is_in_same_broad_category(
        self, requested_category_id: str, product_category_id: str
    ) -> bool:
        req_path = self._registry.get_category_path(requested_category_id)
        prod_path = self._registry.get_category_path(product_category_id)
        if not req_path or not prod_path:
            return False
        return req_path[0] == prod_path[0]


def category_score(
    requested_category_id: str | None,
    product_category_id: str,
    taxonomy: TaxonomyInterface,
) -> float:
    """Compute normalized [0.0, 1.0] category relevance score."""
    if not requested_category_id:
        return 1.0
    req_norm = requested_category_id.strip()
    prod_norm = product_category_id.strip()
    if not req_norm or not prod_norm:
        return CATEGORY_RELEVANCE["UNRELATED"]
    if req_norm == prod_norm:
        return CATEGORY_RELEVANCE["EXACT"]
    if taxonomy.is_related(req_norm, prod_norm):
        return CATEGORY_RELEVANCE["RELATED"]
    if taxonomy.is_in_same_broad_category(req_norm, prod_norm):
        return CATEGORY_RELEVANCE["BROAD"]
    return CATEGORY_RELEVANCE["UNRELATED"]
