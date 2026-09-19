from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from database.models.catalog import CanonicalGarment, MerchantOffer, MerchantProduct
from schemas.catalog.garment_image import GarmentImageCreate
from schemas.catalog.intake import CatalogIntakeRequest


def test_catalog_intake_contract_supports_curated_images() -> None:
    request = CatalogIntakeRequest(
        merchant_id=uuid4(),
        brand_id=uuid4(),
        source_product_id="SKU-001",
        title="Black Cotton T-Shirt",
        source_url="https://example.com/product/SKU-001",
        category="tops",
        subcategory="t_shirt",
        price_minor=99900,
        images=[
            GarmentImageCreate(
                storage_key="product-images/sku-001/front.webp",
                content_hash="a" * 64,
                image_type="front",
            )
        ],
    )
    assert request.images[0].storage_key.endswith("front.webp")


def test_catalog_intake_rejects_negative_price() -> None:
    try:
        CatalogIntakeRequest(
            merchant_id=uuid4(),
            source_product_id="SKU-001",
            title="T",
            source_url="https://example.com/product/SKU-001",
            category="tops",
            price_minor=-1,
        )
    except ValidationError:
        return
    raise AssertionError("negative catalog prices must be rejected")


def test_catalog_schema_contains_explicit_merchant_to_garment_mapping() -> None:
    assert "canonical_garment_id" in MerchantProduct.__table__.columns
    assert "display_name" in CanonicalGarment.__table__.columns
    assert "uq_merchant_offer_source" in {c.name for c in MerchantOffer.__table__.constraints}


def test_catalog_search_query_compiles_for_postgresql() -> None:
    statement = (
        select(CanonicalGarment.id, CanonicalGarment.display_name, MerchantOffer.price_minor)
        .join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
        .where(MerchantOffer.in_stock.is_(True))
    )
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "canonical_garments" in compiled
    assert "merchant_offers" in compiled
