from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    Brand,
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
)
from database.models.catalog_embeddings import (
    ProductImageEmbeddingRecord,
)
from database.models.catalog_freshness import AvailabilityStatus, MerchantOfferSize
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from database.models.catalog_search import ProductSearchDocumentRecord, ProductTextEmbeddingRecord
from database.models.catalog_taxonomy import TaxonomyCategory, TaxonomyVersion


@pytest.fixture
def search_sync_session() -> Session:
    """In-memory SQLite synchronous session with all models created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def setup_search_catalog(search_sync_session: Session) -> dict[str, Any]:
    """Seed comprehensive catalog dataset for testing SRCH-001 through SRCH-040."""
    session = search_sync_session

    # 1. Merchants & Sources
    merch_a = Merchant(
        id=uuid4(),
        name="Merchant A Retail",
        merchant_type="retailer",
        country_code="IN",
        verification_status="VERIFIED",
    )
    merch_b = Merchant(
        id=uuid4(),
        name="Merchant B BrandStore",
        merchant_type="brand",
        country_code="IN",
        verification_status="VERIFIED",
    )
    session.add_all([merch_a, merch_b])

    source_a = CatalogSource(
        id=uuid4(),
        merchant_id=merch_a.id,
        slug=f"src-a-{uuid4().hex[:6]}",
        name="Source A Feed",
        kind="feed_url",
        source_type="FEED",
        access_method="HTTPS_FEED",
        source_status="ACTIVE",
        status="cleared",
        market_codes=["IN"],
        category_codes=["tops", "indian_wear"],
    )
    session.add(source_a)

    perm = CatalogSourcePermission(
        source_id=source_a.id,
        permission_code=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
        permission_status=CatalogPermissionStatus.GRANTED.value,
        granted_by="founder@fashx.internal",
        effective_at=datetime.now(UTC),
    )
    session.add(perm)

    # 2. Brands
    brand_roadster = Brand(id=uuid4(), name="Roadster", normalized_name="roadster")
    brand_fabindia = Brand(id=uuid4(), name="FabIndia", normalized_name="fabindia")
    session.add_all([brand_roadster, brand_fabindia])

    # 3. Taxonomy Hierarchy (Parent Tops -> Child T-Shirt, Parent Indian Wear -> Child Kurta)
    tax_ver = TaxonomyVersion(
        id=uuid4(),
        version="1.0.0",
        status="ACTIVE",
        locale="en-IN",
        market="IN",
        description="Standard Taxonomy",
    )
    session.add(tax_ver)
    session.flush()

    cat_tops = TaxonomyCategory(
        id=uuid4(),
        taxonomy_version_id=tax_ver.id,
        category_code="tops",
        parent_code=None,
        label="Tops",
        path="apparel.tops",
        level=1,
        is_leaf=False,
    )
    cat_indian = TaxonomyCategory(
        id=uuid4(),
        taxonomy_version_id=tax_ver.id,
        category_code="indian_wear",
        parent_code=None,
        label="Indian Wear",
        path="apparel.indian_wear",
        level=1,
        is_leaf=False,
    )
    session.add_all([cat_tops, cat_indian])
    session.flush()

    cat_tshirt = TaxonomyCategory(
        id=uuid4(),
        taxonomy_version_id=tax_ver.id,
        category_code="t_shirts",
        parent_code="tops",
        label="T-Shirts",
        path="apparel.tops.t_shirts",
        level=2,
        is_leaf=True,
    )
    cat_kurta = TaxonomyCategory(
        id=uuid4(),
        taxonomy_version_id=tax_ver.id,
        category_code="kurtas",
        parent_code="indian_wear",
        label="Kurtas",
        path="apparel.indian_wear.kurtas",
        level=2,
        is_leaf=True,
    )
    session.add_all([cat_tshirt, cat_kurta])

    # 4. Canonical Garments & Products
    g1 = CanonicalGarment(
        id=uuid4(),
        brand_id=brand_roadster.id,
        display_name="Men's Black Casual Shirt",
        category="tops",
        color_family="black",
    )
    g2 = CanonicalGarment(
        id=uuid4(),
        brand_id=brand_fabindia.id,
        display_name="Men's Navy Blue Kurta",
        category="indian_wear",
        color_family="navy_blue",
    )
    session.add_all([g1, g2])
    session.flush()

    # Product 1: Black Casual Shirt (Roadster, Tops/T-shirt, ₹899, Sizes: M in stock, L out of stock)
    mp1 = MerchantProduct(
        id=uuid4(),
        merchant_id=merch_a.id,
        canonical_garment_id=g1.id,
        source_id=source_a.id,
        brand_id=brand_roadster.id,
        source_product_id="SKU-SHIRT-01",
        title="Men's Black Casual Shirt",
        description="Comfortable pure cotton black shirt for casual and office wear.",
        source_url="https://merchant-a.com/black-shirt",
        price_minor=899,
        currency="INR",
        status="active",
        availability="IN_STOCK",
    )
    # Product 2: Navy Blue Kurta (FabIndia, Indian Wear/Kurta, ₹1,499, Sizes: 38 in stock)
    mp2 = MerchantProduct(
        id=uuid4(),
        merchant_id=merch_a.id,
        canonical_garment_id=g2.id,
        source_id=source_a.id,
        brand_id=brand_fabindia.id,
        source_product_id="SKU-KURTA-02",
        title="Men's Navy Blue Kurta",
        description="Traditional festive ethnic wear navy blue cotton kurta.",
        source_url="https://merchant-a.com/navy-kurta",
        price_minor=1499,
        currency="INR",
        status="active",
        availability="IN_STOCK",
    )
    # Product 3: Striped Casual Tee (Roadster, Tops, ₹499, Sizes: M out of stock, XL in stock)
    mp3 = MerchantProduct(
        id=uuid4(),
        merchant_id=merch_a.id,
        canonical_garment_id=g1.id,
        source_id=source_a.id,
        brand_id=brand_roadster.id,
        source_product_id="SKU-TEE-03",
        title="Striped Cotton Casual T-Shirt",
        description="Relaxed fit striped tee for summer everyday casual wear.",
        source_url="https://merchant-a.com/striped-tee",
        price_minor=499,
        currency="INR",
        status="active",
        availability="IN_STOCK",
    )
    session.add_all([mp1, mp2, mp3])
    session.flush()

    # 5. Active Offers & Sizes
    offer1 = MerchantOffer(
        id=uuid4(),
        garment_id=g1.id,
        merchant_id=merch_a.id,
        merchant_product_id=mp1.id,
        source_product_id="SKU-SHIRT-01",
        url="https://merchant-a.com/shirt",
        price_minor=89900,
        currency="INR",
        status="ACTIVE",
    )
    offer2 = MerchantOffer(
        id=uuid4(),
        garment_id=g2.id,
        merchant_id=merch_a.id,
        merchant_product_id=mp2.id,
        source_product_id="SKU-KURTA-02",
        url="https://merchant-a.com/kurta",
        price_minor=149900,
        currency="INR",
        status="ACTIVE",
    )
    offer3 = MerchantOffer(
        id=uuid4(),
        garment_id=g1.id,
        merchant_id=merch_a.id,
        merchant_product_id=mp3.id,
        source_product_id="SKU-TEE-03",
        url="https://merchant-a.com/tee",
        price_minor=49900,
        currency="INR",
        status="ACTIVE",
    )
    session.add_all([offer1, offer2, offer3])
    session.flush()

    # Sizing
    # mp1: M (IN_STOCK), L (OUT_OF_STOCK)
    sz1_m = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer1.id,
        raw_size="M",
        availability=AvailabilityStatus.IN_STOCK.value,
        stock_quantity=10,
    )
    sz1_l = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer1.id,
        raw_size="L",
        availability=AvailabilityStatus.OUT_OF_STOCK.value,
        stock_quantity=0,
    )
    # mp2: 38 (IN_STOCK), 40 (UNKNOWN)
    sz2_38 = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer2.id,
        raw_size="38",
        availability=AvailabilityStatus.IN_STOCK.value,
        stock_quantity=5,
    )
    sz2_40 = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer2.id,
        raw_size="40",
        availability="UNKNOWN",
        stock_quantity=None,
    )
    # mp3: M (OUT_OF_STOCK), XL (IN_STOCK)
    sz3_m = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer3.id,
        raw_size="M",
        availability=AvailabilityStatus.OUT_OF_STOCK.value,
        stock_quantity=0,
    )
    sz3_xl = MerchantOfferSize(
        id=uuid4(),
        merchant_offer_id=offer3.id,
        raw_size="XL",
        availability=AvailabilityStatus.IN_STOCK.value,
        stock_quantity=8,
    )
    session.add_all([sz1_m, sz1_l, sz2_38, sz2_40, sz3_m, sz3_xl])

    # 6. Search Documents
    doc1 = ProductSearchDocumentRecord(
        id=uuid4(),
        merchant_product_id=mp1.id,
        product_id=g1.id,
        merchant_id=merch_a.id,
        brand_id=brand_roadster.id,
        category_id=cat_tshirt.id,
        subcategory_id=cat_tshirt.id,
        title=mp1.title,
        description=mp1.description,
        search_document="mens black casual shirt pure cotton",
        taxonomy_version="1.0.0",
        enrichment_version="1.0.0",
        indexed_attributes_json={
            "color": "black",
            "garment_type": "shirt",
            "occasion": "casual",
            "fabric": "cotton",
            "confidence": 0.98,
        },
    )
    doc2 = ProductSearchDocumentRecord(
        id=uuid4(),
        merchant_product_id=mp2.id,
        product_id=g2.id,
        merchant_id=merch_a.id,
        brand_id=brand_fabindia.id,
        category_id=cat_kurta.id,
        subcategory_id=cat_kurta.id,
        title=mp2.title,
        description=mp2.description,
        search_document="mens navy blue kurta festive ethnic wear",
        taxonomy_version="1.0.0",
        enrichment_version="1.0.0",
        indexed_attributes_json={
            "color": "navy_blue",
            "garment_type": "kurta",
            "occasion": "festive",
            "fabric": "cotton",
            "confidence": 0.99,
        },
    )
    doc3 = ProductSearchDocumentRecord(
        id=uuid4(),
        merchant_product_id=mp3.id,
        product_id=g1.id,
        merchant_id=merch_a.id,
        brand_id=brand_roadster.id,
        category_id=cat_tshirt.id,
        subcategory_id=cat_tshirt.id,
        title=mp3.title,
        description=mp3.description,
        search_document="striped cotton casual t shirt relaxed fit",
        taxonomy_version="1.0.0",
        enrichment_version="1.0.0",
        indexed_attributes_json={
            "color": "multi",
            "garment_type": "t_shirt",
            "occasion": "casual",
            "fabric": "cotton",
            "confidence": 0.95,
        },
    )
    session.add_all([doc1, doc2, doc3])

    # 7. Semantic Text Embeddings
    from fashx.catalog.embeddings.models.mock_adapter import MockViTB32Adapter

    mock_emb_adapter = MockViTB32Adapter()
    vec1 = mock_emb_adapter.embed_text(["formal office shirt"])[0]
    vec2 = mock_emb_adapter.embed_text(["navy blue festive kurta"])[0]
    vec3 = mock_emb_adapter.embed_text(["striped casual cotton t shirt"])[0]

    txt_emb1 = ProductTextEmbeddingRecord(
        id=uuid4(),
        merchant_product_id=mp1.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        text_revision_hash="hash1",
        embedding_dimension=512,
        embedding=vec1,
        status="READY",
    )
    txt_emb2 = ProductTextEmbeddingRecord(
        id=uuid4(),
        merchant_product_id=mp2.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        text_revision_hash="hash2",
        embedding_dimension=512,
        embedding=vec2,
        status="READY",
    )
    txt_emb3 = ProductTextEmbeddingRecord(
        id=uuid4(),
        merchant_product_id=mp3.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        text_revision_hash="hash3",
        embedding_dimension=512,
        embedding=vec3,
        status="READY",
    )
    session.add_all([txt_emb1, txt_emb2, txt_emb3])

    # 8. Visual Image Assets & Embeddings
    asset1 = CatalogImageAsset(
        id=uuid4(),
        source_id=source_a.id,
        merchant_id=merch_a.id,
        source_product_id="SKU-SHIRT-01",
        status=ImageAssetStatus.ACTIVE.value,
        original_sha256="sha_img_1",
        normalized_sha256="sha_img_1",
    )
    asset2 = CatalogImageAsset(
        id=uuid4(),
        source_id=source_a.id,
        merchant_id=merch_a.id,
        source_product_id="SKU-KURTA-02",
        status=ImageAssetStatus.ACTIVE.value,
        original_sha256="sha_img_2",
        normalized_sha256="sha_img_2",
    )
    session.add_all([asset1, asset2])
    session.flush()

    img_emb1 = ProductImageEmbeddingRecord(
        id=uuid4(),
        image_asset_id=asset1.id,
        product_id=mp1.id,
        merchant_id=merch_a.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec1,
        image_sha256="sha_img_1",
        status="ACTIVE",
        is_active=True,
    )
    img_emb2 = ProductImageEmbeddingRecord(
        id=uuid4(),
        image_asset_id=asset2.id,
        product_id=mp2.id,
        merchant_id=merch_a.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec2,
        image_sha256="sha_img_2",
        status="ACTIVE",
        is_active=True,
    )
    session.add_all([img_emb1, img_emb2])

    session.commit()

    return {
        "merch_a": merch_a,
        "merch_b": merch_b,
        "source_a": source_a,
        "brand_roadster": brand_roadster,
        "brand_fabindia": brand_fabindia,
        "cat_tops": cat_tops,
        "cat_indian": cat_indian,
        "cat_tshirt": cat_tshirt,
        "cat_kurta": cat_kurta,
        "mp1": mp1,
        "mp2": mp2,
        "mp3": mp3,
        "offer1": offer1,
        "offer2": offer2,
        "offer3": offer3,
        "asset1": asset1,
        "asset2": asset2,
    }
