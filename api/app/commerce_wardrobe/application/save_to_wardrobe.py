from dataclasses import dataclass
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.errors import EntityNotFoundError
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from database.models.commerce_feedback import WardrobeItem


@dataclass(frozen=True)
class SaveToWardrobeCommand:
    user_id: UUID
    garment_id: UUID
    offer_id: UUID | None = None
    tryon_artifact_id: UUID | None = None


@dataclass(frozen=True)
class SaveToWardrobeResult:
    item_id: UUID
    user_id: UUID
    garment_id: UUID
    snapshot_title: str
    snapshot_price_minor: int
    snapshot_currency: str
    snapshot_image_key: str
    tryon_artifact_id: UUID | None


class SaveToWardrobeUseCase:
    """Saves a garment to user's virtual closet with immutable snapshot metadata (Rule I11)."""

    def __init__(
        self,
        wardrobe_uow: CommerceWardrobeUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
    ) -> None:
        self.wardrobe_uow = wardrobe_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow

    async def execute(self, cmd: SaveToWardrobeCommand) -> SaveToWardrobeResult:
        # 1. Validate User
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

        # 2. Retrieve Garment & Snapshot Context
        async with self.catalog_uow:
            garment = await self.catalog_uow.canonical_garments.get_by_id(cmd.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.garment_id)

            # Determine snapshot price
            price_minor = 0
            currency = "INR"
            offer_id = cmd.offer_id

            if offer_id:
                offer = await self.catalog_uow.offers.get_by_id(offer_id)
                if offer:
                    price_minor = offer.price_minor
                    currency = offer.currency
            else:
                offers = await self.catalog_uow.offers.list_for_garment(garment.id)
                if offers:
                    top_offer = offers[0]
                    offer_id = top_offer.id
                    price_minor = top_offer.price_minor
                    currency = top_offer.currency

            # Determine snapshot title
            snapshot_title = (
                f"{garment.category.replace('_', ' ').title()} ({garment.subcategory or 'Classic'})"
            )
            if offer_id:
                offer = await self.catalog_uow.offers.get_by_id(offer_id)
                if offer:
                    product = await self.catalog_uow.merchant_products.get_by_source_id(
                        offer.merchant_id, offer.source_product_id
                    )
                    if product:
                        snapshot_title = product.title

            # Determine snapshot image
            images = await self.catalog_uow.images.list_for_garment(garment.id)
            snapshot_image_key = images[0].s3_key if images else f"garments/{garment.id}/front.png"

        # 3. Save or Update in Wardrobe
        async with self.wardrobe_uow:
            existing = await self.wardrobe_uow.wardrobe.get_by_user_and_garment(
                cmd.user_id, cmd.garment_id
            )
            if existing:
                existing.offer_id = offer_id
                existing.snapshot_title = snapshot_title
                existing.snapshot_price_minor = price_minor
                existing.snapshot_currency = currency
                existing.snapshot_image_key = snapshot_image_key
                if cmd.tryon_artifact_id:
                    existing.tryon_artifact_id = cmd.tryon_artifact_id
                await self.wardrobe_uow.commit()

                return SaveToWardrobeResult(
                    item_id=existing.id,
                    user_id=existing.user_id,
                    garment_id=existing.garment_id,
                    snapshot_title=existing.snapshot_title,
                    snapshot_price_minor=existing.snapshot_price_minor,
                    snapshot_currency=existing.snapshot_currency,
                    snapshot_image_key=existing.snapshot_image_key,
                    tryon_artifact_id=existing.tryon_artifact_id,
                )

            item = WardrobeItem(
                user_id=cmd.user_id,
                garment_id=cmd.garment_id,
                offer_id=offer_id,
                snapshot_title=snapshot_title,
                snapshot_price_minor=price_minor,
                snapshot_currency=currency,
                snapshot_image_key=snapshot_image_key,
                tryon_artifact_id=cmd.tryon_artifact_id,
            )
            self.wardrobe_uow.wardrobe.add(item)
            await self.wardrobe_uow.commit()

            return SaveToWardrobeResult(
                item_id=item.id,
                user_id=item.user_id,
                garment_id=item.garment_id,
                snapshot_title=item.snapshot_title,
                snapshot_price_minor=item.snapshot_price_minor,
                snapshot_currency=item.snapshot_currency,
                snapshot_image_key=item.snapshot_image_key,
                tryon_artifact_id=item.tryon_artifact_id,
            )
