from __future__ import annotations

from uuid import UUID

from api.app.core.errors import NotFoundError
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.tryon.domain.input_assembly import validate_garment_for_tryon


class LocalCatalogTryOnClient:
    """Modular-monolith adapter; replaceable by an HTTP client after service extraction."""

    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    async def get_garment_for_tryon(self, *, garment_id: UUID) -> dict:
        garment = await self.repository.get_garment(garment_id)
        if garment is None:
            raise NotFoundError("Try-on garment not found")
        images = await self.repository.get_images(garment_id)
        image = next((x for x in images if x.image_type == "model"), None) or next(
            (x for x in images if x.image_type == "front"), None
        )
        validate_garment_for_tryon(category=garment.category, image_key=image.storage_key if image else None)
        assert image is not None
        return {
            "garment_id": garment.id,
            "version": garment.version,
            "category": garment.category,
            "image_key": image.storage_key,
            "image_version": image.version,
            "image_id": image.id,
        }
