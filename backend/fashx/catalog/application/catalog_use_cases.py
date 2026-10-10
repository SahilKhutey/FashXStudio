from __future__ import annotations

from uuid import UUID

from fashx.catalog.repositories.catalog import CatalogRepository
from fashx.core.transactions import transaction


class CatalogApplicationService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    async def create_garment(self, *, category: str, subcategory: str | None = None, brand_id: UUID | None = None) -> UUID:
        async with transaction(self.repository.session):
            garment = await self.repository.create_garment(
                category=category,
                subcategory=subcategory,
                brand_id=brand_id,
            )
            return garment.id
