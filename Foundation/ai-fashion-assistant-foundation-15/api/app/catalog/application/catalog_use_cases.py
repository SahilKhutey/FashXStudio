from __future__ import annotations

from uuid import UUID

from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.transactions import transaction
from schemas.catalog.intake import CatalogIntakeRequest, CatalogIntakeResponse


class CatalogApplicationService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    async def create_garment(
        self, *, display_name: str, category: str, subcategory: str | None = None, brand_id: UUID | None = None
    ) -> UUID:
        async with transaction(self.repository.session):
            garment = await self.repository.create_garment(
                display_name=display_name,
                category=category,
                subcategory=subcategory,
                brand_id=brand_id,
            )
            return garment.id

    async def intake_listing(self, payload: CatalogIntakeRequest) -> CatalogIntakeResponse:
        async with transaction(self.repository.session):
            merchant = await self.repository.get_merchant_by_id(payload.merchant_id)
            if merchant is None:
                raise ValueError("Merchant not found")

            merchant_product, merchant_product_created = await self.repository.upsert_merchant_product(
                merchant_id=payload.merchant_id,
                brand_id=payload.brand_id,
                source_product_id=payload.source_product_id,
                title=payload.title,
                description=payload.description,
                source_url=str(payload.source_url),
            )

            if merchant_product.canonical_garment_id:
                garment = await self.repository.get_garment(merchant_product.canonical_garment_id)
                if garment is None:
                    garment = await self.repository.create_garment(
                        display_name=payload.title,
                        category=payload.category,
                        subcategory=payload.subcategory,
                        brand_id=payload.brand_id,
                    )
                    merchant_product.canonical_garment_id = garment.id
                    await self.repository.session.flush()
                    garment_created = True
                else:
                    garment_created = False
                    await self.repository.update_garment(
                        garment,
                        display_name=payload.title,
                        category=payload.category,
                        subcategory=payload.subcategory,
                        brand_id=payload.brand_id,
                    )
            else:
                garment = await self.repository.create_garment(
                    display_name=payload.title,
                    category=payload.category,
                    subcategory=payload.subcategory,
                    brand_id=payload.brand_id,
                )
                merchant_product.canonical_garment_id = garment.id
                await self.repository.session.flush()
                garment_created = True

            offer, offer_created = await self.repository.upsert_offer(
                garment_id=garment.id,
                merchant_id=payload.merchant_id,
                source_product_id=payload.source_product_id,
                url=str(payload.source_url),
                price_minor=payload.price_minor,
                currency=payload.currency.upper(),
            )

            images_created = 0
            for image in payload.images:
                _, created = await self.repository.upsert_image(
                    garment_id=garment.id,
                    storage_key=image.storage_key,
                    content_hash=image.content_hash,
                    perceptual_hash=image.perceptual_hash,
                    image_type=image.image_type.value,
                )
                images_created += int(created)

            operation = "created" if merchant_product_created or garment_created or offer_created else "updated"
            return CatalogIntakeResponse(
                product_id=garment.id,
                merchant_product_id=merchant_product.id,
                operation=operation,
                enrichment_required=garment_created or images_created > 0,
                ocr_required=garment_created,
                image_count=len(await self.repository.get_images(garment.id)),
            )
