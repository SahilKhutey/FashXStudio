from dataclasses import dataclass
from uuid import UUID

from database.models.catalog import CanonicalGarment, CatalogSource, MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError


@dataclass
class IngestProductCommand:
    merchant_id: UUID
    source_product_id: str
    title: str
    source_url: str
    category: str
    price_minor: int
    subcategory: str | None = None
    description: str | None = None
    currency: str = "INR"
    in_stock: bool = True
    brand_id: UUID | None = None
    source_id: UUID | None = None
    item_group_id: str | None = None
    content_hash: str | None = None
    status: str = "active"


@dataclass
class IngestProductResult:
    merchant_product_id: UUID
    canonical_garment_id: UUID
    offer_id: UUID
    title: str
    category: str
    price_minor: int
    currency: str


class IngestMerchantProductUseCase:
    """Use case to ingest merchant products, establish canonical garments, and link merchant offers."""

    def __init__(self, uow: CatalogUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: IngestProductCommand) -> IngestProductResult:
        if cmd.price_minor < 0:
            raise ValidationError("Price cannot be negative", field="price_minor")

        async with self.uow:
            merchant = await self.uow.merchants.get_by_id(cmd.merchant_id)
            if merchant is None:
                raise EntityNotFoundError("Merchant", cmd.merchant_id)

            # Determine source_id (fallback to merchant default cleared source)
            source_id = cmd.source_id
            if source_id is None:
                default_slug = f"merchant-{cmd.merchant_id}"
                source = await self.uow.sources.get_by_slug(default_slug)
                if source is None:
                    source = CatalogSource(
                        slug=default_slug,
                        name=merchant.name,
                        kind="manual",
                        status="cleared",
                        rights_display=True,
                        rights_tryon=True,
                        image_policy="mirror",
                    )
                    self.uow.sources.add(source)
                    await self.uow.sources.flush()
                source_id = source.id

            # 1. Upsert MerchantProduct
            product = await self.uow.merchant_products.get_by_source_id(
                cmd.merchant_id, cmd.source_product_id
            )
            if product is not None:
                product.title = cmd.title
                product.description = cmd.description
                product.source_url = cmd.source_url
                product.brand_id = cmd.brand_id
                product.source_id = source_id
                product.item_group_id = cmd.item_group_id
                product.content_hash = cmd.content_hash
                product.status = cmd.status
            else:
                product = MerchantProduct(
                    merchant_id=cmd.merchant_id,
                    brand_id=cmd.brand_id,
                    source_id=source_id,
                    source_product_id=cmd.source_product_id,
                    item_group_id=cmd.item_group_id,
                    content_hash=cmd.content_hash,
                    status=cmd.status,
                    title=cmd.title,
                    description=cmd.description,
                    source_url=cmd.source_url,
                )
                self.uow.merchant_products.add(product)
            await self.uow.merchant_products.flush()

            # 2. Link or create CanonicalGarment
            existing_offer = await self.uow.offers.get_by_merchant_and_product(
                cmd.merchant_id, cmd.source_product_id
            )
            if existing_offer is not None:
                garment_id = existing_offer.garment_id
            else:
                garment = CanonicalGarment(
                    brand_id=cmd.brand_id,
                    category=cmd.category,
                    subcategory=cmd.subcategory,
                    version=1,
                )
                self.uow.canonical_garments.add(garment)
                await self.uow.canonical_garments.flush()
                garment_id = garment.id

            # 3. Upsert MerchantOffer
            offer = await self.uow.offers.upsert_offer(
                garment_id=garment_id,
                merchant_id=cmd.merchant_id,
                source_product_id=cmd.source_product_id,
                url=cmd.source_url,
                price_minor=cmd.price_minor,
                currency=cmd.currency,
                in_stock=cmd.in_stock,
            )
            await self.uow.offers.flush()

            await self.uow.commit()

            return IngestProductResult(
                merchant_product_id=product.id,
                canonical_garment_id=garment_id,
                offer_id=offer.id,
                title=product.title,
                category=cmd.category,
                price_minor=offer.price_minor,
                currency=offer.currency,
            )
