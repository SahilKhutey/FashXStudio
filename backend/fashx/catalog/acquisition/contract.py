"""Source adapter contracts and data transfer objects for catalog acquisition."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class SourceProduct:
    """Canonical representation of an apparel item as fetched from an external source."""

    source_slug: str
    source_product_id: str
    title: str
    category: str
    price_minor: int
    currency: str = "INR"
    product_url: str = ""
    brand: str | None = None
    subcategory: str | None = None
    description: str | None = None
    image_url: str | None = None
    in_stock: bool | None = True
    sizes: tuple[str, ...] = ()
    source_updated_at: str | None = None
    image_rights: str = "partner_authorized"  # owned | licensed | partner_authorized
    tryon_rights: bool = False
    raw_attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcquisitionBatch:
    """A batch of acquired source products with pagination state."""

    source_slug: str
    products: Sequence[SourceProduct]
    cursor: str | None = None
    has_more: bool = False
    total_found: int | None = None


@runtime_checkable
class CatalogSourceAdapter(Protocol):
    """Protocol defining the interface for all store-specific catalog adapters."""

    @property
    def source_slug(self) -> str:
        """Stable slug identifying the source (e.g. 'amazon', 'myntra', 'flipkart')."""
        ...

    async def fetch_batch(
        self,
        cursor: str | None = None,
        limit: int = 100,
    ) -> AcquisitionBatch:
        """Fetch the next batch of catalog products from the source."""
        ...
