from __future__ import annotations

from uuid import UUID

from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.errors import ConflictError, NotFoundError
from api.app.core.transactions import transaction
from api.app.wardrobe.repository import WardrobeRepository
from schemas.catalog.detail import RejectCatalogItemResponse, SaveCatalogItemRequest, SaveCatalogItemResponse


class WardrobeDecisionService:
    def __init__(self, wardrobe: WardrobeRepository, catalog: CatalogRepository) -> None:
        self.wardrobe = wardrobe
        self.catalog = catalog

    async def save(self, user_id: UUID, garment_id: UUID, request: SaveCatalogItemRequest) -> SaveCatalogItemResponse:
        async with transaction(self.catalog.session):
            garment = await self.catalog.get_garment(garment_id)
            if garment is None:
                raise NotFoundError("Catalog product not found")

            offer = None
            if request.offer_id:
                try:
                    offer_id = UUID(request.offer_id)
                except ValueError as exc:
                    raise ConflictError("offer_id is invalid") from exc
                offer = await self.catalog.get_offer(garment_id, offer_id)
                if offer is None:
                    raise NotFoundError("Selected merchant offer not found")

            images = await self.catalog.get_images(garment_id)
            selected_image = None
            if request.snapshot_image_id:
                selected_image = next((img for img in images if str(img.id) == request.snapshot_image_id), None)
                if selected_image is None:
                    raise NotFoundError("Selected product image not found")
            else:
                selected_image = next((img for img in images if img.image_type in {"front", "model"}), None)
                if selected_image is None and images:
                    selected_image = images[0]

            if selected_image is None:
                raise ConflictError("Catalog item has no image available to save")

            item, created = await self.wardrobe.save_item(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=offer.id if offer else None,
                snapshot_title=garment.display_name,
                snapshot_price_minor=offer.price_minor if offer else 0,
                snapshot_currency=offer.currency if offer else "INR",
                snapshot_image_key=selected_image.storage_key,
            )
            return SaveCatalogItemResponse(
                wardrobe_item_id=str(item.id),
                garment_id=str(garment_id),
                offer_id=str(item.offer_id) if item.offer_id else None,
                already_saved=not created,
            )

    async def reject(self, user_id: UUID, garment_id: UUID) -> RejectCatalogItemResponse:
        async with transaction(self.catalog.session):
            if await self.catalog.get_garment(garment_id) is None:
                raise NotFoundError("Catalog product not found")
            await self.wardrobe.reject(user_id, garment_id)
            return RejectCatalogItemResponse(garment_id=str(garment_id))
