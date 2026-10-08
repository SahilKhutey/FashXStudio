from __future__ import annotations

from uuid import UUID

from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.errors import NotFoundError


class OfferSelectionService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    async def validate_selection(self, garment_id: UUID, offer_id: UUID):
        offer = await self.catalog.get_offer(garment_id, offer_id)
        if offer is None:
            raise NotFoundError("Merchant offer not found")
        if not offer.in_stock:
            raise NotFoundError("Selected merchant offer is unavailable")
        return offer
