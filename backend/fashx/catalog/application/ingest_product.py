import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from database.models.catalog import CanonicalGarment, CatalogSource, GarmentImage, MerchantProduct
from fashx.catalog.eligibility import compute_tryon_eligibility
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError

VALID_TAXONOMY_CATEGORIES = {
    "top",
    "tops",
    "shirt",
    "shirts",
    "tshirt",
    "tshirts",
    "bottom",
    "bottoms",
    "pants",
    "trousers",
    "jeans",
    "skirts",
    "one_piece",
    "one-piece",
    "one-pieces",
    "dress",
    "dresses",
    "jumpsuit",
    "outerwear",
    "jacket",
    "jackets",
    "coat",
    "coats",
    "sweater",
    "sweaters",
    "hoodie",
    "hoodies",
    "kurta",
    "kurtas",
    "ethnic",
}


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
    sizes_in_stock: list[str] = field(default_factory=list)
    brand_id: UUID | None = None
    source_id: UUID | None = None
    item_group_id: str | None = None
    content_hash: str | None = None
    status: str = "active"
    image_url: str | None = None
    image_rights: str | None = None
    tryon_rights: bool | None = None


@dataclass
class IngestProductResult:
    merchant_product_id: UUID
    canonical_garment_id: UUID
    offer_id: UUID
    title: str
    category: str
    price_minor: int
    currency: str
    image_id: UUID | None = None
    tryon_supported: bool = False


class IngestMerchantProductUseCase:
    """Use case to ingest merchant products, establish canonical garments, and link merchant offers."""

    def __init__(self, uow: CatalogUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: IngestProductCommand) -> IngestProductResult:
        cat_normalized = cmd.category.strip().lower() if cmd.category else ""
        if not cat_normalized or cat_normalized not in VALID_TAXONOMY_CATEGORIES:
            raise ValidationError(
                f"Unknown category '{cmd.category}' not in approved taxonomy", field="category"
            )

        title = cmd.title.strip() if cmd.title else ""
        effective_title = (
            title
            or (cmd.subcategory.strip() if cmd.subcategory else "")
            or cat_normalized
        )
        if not effective_title:
            raise ValidationError("Product title cannot be empty", field="title")

        if cmd.price_minor < 0:
            raise ValidationError("Price cannot be negative", field="price_minor")

        if not cmd.source_url or not (
            cmd.source_url.startswith("http://") or cmd.source_url.startswith("https://")
        ):
            raise ValidationError(
                "Invalid or malformed product destination URL", field="source_url"
            )

        if cmd.image_url and not (
            cmd.image_url.startswith("http://") or cmd.image_url.startswith("https://")
        ):
            raise ValidationError(
                "Invalid or malformed product image URL", field="image_url"
            )

        async with self.uow:
            merchant = await self.uow.merchants.get_by_id(cmd.merchant_id)
            if merchant is None:
                raise EntityNotFoundError("Merchant", cmd.merchant_id)

            # Determine source_id (must be pre-registered or default fallback in unapproved status)
            source_id = cmd.source_id
            if source_id is not None:
                source = await self.uow.sources.get_by_id(source_id)
                if source is None:
                    raise EntityNotFoundError("CatalogSource", source_id)
            else:
                default_slug = f"merchant-{cmd.merchant_id}"
                source = await self.uow.sources.get_by_slug(default_slug)
                if source is None:
                    source = CatalogSource(
                        slug=default_slug,
                        name=merchant.name,
                        kind="manual",
                        status="pending_approval",
                        rights_display=False,
                        rights_tryon=False,
                        image_policy="mirror",
                    )
                    self.uow.sources.add(source)
                    await self.uow.sources.flush()
                source_id = source.id

            now = datetime.now(UTC)

            # Calculate try-on eligibility (requires source approval + product-level permission if specified)
            rights_tryon = source.rights_tryon if source else False
            if cmd.tryon_rights is not None:
                rights_tryon = rights_tryon and cmd.tryon_rights
            image_policy = source.image_policy if source else "hotlink"
            is_eligible = compute_tryon_eligibility(
                source_rights_tryon=rights_tryon,
                source_image_policy=image_policy,
                category=cmd.category,
            )

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
                product.last_seen_at = now
                product.price_checked_at = now
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
                    last_seen_at=now,
                    price_checked_at=now,
                )
                self.uow.merchant_products.add(product)
            await self.uow.merchant_products.flush()

            # 2. Link or create CanonicalGarment
            existing_offer = await self.uow.offers.get_by_merchant_and_product(
                cmd.merchant_id, cmd.source_product_id
            )
            if existing_offer is not None:
                garment_id = existing_offer.garment_id
                existing_garment = await self.uow.canonical_garments.get_by_id(garment_id)
                if existing_garment is not None:
                    existing_garment.price_updated_at = now
                    existing_garment.in_stock = cmd.in_stock
                    existing_garment.tryon_supported = is_eligible
                    if cmd.sizes_in_stock:
                        existing_garment.sizes_in_stock = cmd.sizes_in_stock
            else:
                garment = CanonicalGarment(
                    brand_id=cmd.brand_id,
                    category=cmd.category,
                    subcategory=cmd.subcategory,
                    display_name=cmd.title or cmd.subcategory or cmd.category or "",
                    price_minor=cmd.price_minor,
                    sizes_in_stock=cmd.sizes_in_stock,
                    price_updated_at=now,
                    version=1,
                    in_stock=cmd.in_stock,
                    tryon_supported=is_eligible,
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
            offer.last_synced_at = now
            await self.uow.offers.flush()

            # 4. Optional Image Ingestion
            image_id = None
            if cmd.image_url:
                img_hash = cmd.content_hash or hashlib.sha256(cmd.image_url.encode("utf-8")).hexdigest()
                existing_img = await self.uow.images.get_by_hash(img_hash)
                if existing_img is None:
                    g_img = GarmentImage(
                        garment_id=garment_id,
                        storage_key=cmd.image_url,
                        content_hash=img_hash,
                        image_type="catalog",
                    )
                    self.uow.images.add(g_img)
                    await self.uow.images.flush()
                    image_id = g_img.id
                else:
                    image_id = existing_img.id

            await self.uow.commit()

            return IngestProductResult(
                merchant_product_id=product.id,
                canonical_garment_id=garment_id,
                offer_id=offer.id,
                title=product.title,
                category=cmd.category,
                price_minor=offer.price_minor,
                currency=offer.currency,
                image_id=image_id,
                tryon_supported=is_eligible,
            )
