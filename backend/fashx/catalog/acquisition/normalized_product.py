"""Canonical normalized product data transfer objects for catalog acquisition."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

Availability = Literal[
    "in_stock",
    "out_of_stock",
    "preorder",
    "backorder",
    "discontinued",
    "unknown",
]


@dataclass(frozen=True)
class NormalizedProduct:
    """Canonical representation of an apparel product normalized from source feeds."""

    source_id: UUID
    merchant_id: UUID
    source_product_id: str
    title: str
    category: str
    subcategory: str | None
    price_minor: int
    currency: str
    product_url: str
    availability: Availability
    brand: str | None = None
    brand_id: UUID | None = None
    description: str | None = None
    sizes: tuple[str, ...] = ()
    raw_sizes: tuple[str, ...] = ()
    color: str | None = None
    raw_color: str | None = None
    image_url: str | None = None
    prepared_image_key: str | None = None
    prepared_image_hash: str | None = None
    display_eligible: bool = False
    tryon_eligible: bool = False
    source_updated_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_attributes: dict[str, Any] = field(default_factory=dict)

    def compute_content_hash(self) -> str:
        """Compute deterministic SHA-256 hash over normalized fields."""
        raw = (
            f"{self.source_product_id}|{self.title}|{self.brand or ''}|"
            f"{self.category}|{self.subcategory or ''}|"
            f"{self.price_minor}|{self.currency}|{self.product_url}|"
            f"{self.availability}|{','.join(self.sizes)}|{self.color or ''}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
