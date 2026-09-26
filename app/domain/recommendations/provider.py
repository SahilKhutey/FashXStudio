from decimal import Decimal
from typing import Protocol
from uuid import UUID


class PersonalizationProvider(Protocol):
    async def score(
        self,
        customer_id: UUID,
        *,
        category: str | None = None,
        brand: str | None = None,
        style: str | None = None,
        color: str | None = None,
        material: str | None = None,
        occasion: str | None = None,
        region: str | None = None,
    ) -> Decimal:
        ...


class DefaultPersonalizationProvider:
    """Default fallback personalization provider returning zero personalization score."""

    async def score(
        self,
        customer_id: UUID,
        *,
        category: str | None = None,
        brand: str | None = None,
        style: str | None = None,
        color: str | None = None,
        material: str | None = None,
        occasion: str | None = None,
        region: str | None = None,
    ) -> Decimal:
        return Decimal("0")
