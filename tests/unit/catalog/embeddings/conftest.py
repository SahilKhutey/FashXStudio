from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
)
from database.models.catalog_embeddings import EmbeddingModelRegistryRecord
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus


@pytest.fixture
def sync_db_session() -> Session:
    """Create in-memory SQLite sync database session with all tables created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Pre-seed approved openclip model
    model_reg = EmbeddingModelRegistryRecord(
        model_id="openclip_vit_b32",
        model_version="v1",
        dimension=512,
        status="APPROVED",
        architecture="ViT-B/32",
        framework="openclip",
        metadata_json={},
    )
    session.add(model_reg)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a valid 200x200 RGB JPEG image."""
    img = Image.new("RGB", (200, 200), color=(120, 50, 180))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_png_rgba_bytes() -> bytes:
    """Generate a valid 250x150 RGBA PNG image with transparency."""
    img = Image.new("RGBA", (250, 150), color=(200, 100, 50, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def setup_catalog_image_asset(sync_db_session: Session, sample_image_bytes: bytes) -> tuple[Merchant, CatalogImageAsset]:
    """Create a verified merchant, active source with permission, and active image asset."""
    merchant = Merchant(
        id=uuid4(),
        name=f"Merchant {uuid4().hex[:6]}",
        merchant_type="brand",
        country_code="IN",
        verification_status="VERIFIED",
    )
    sync_db_session.add(merchant)

    source = CatalogSource(
        id=uuid4(),
        merchant_id=merchant.id,
        slug=f"source-{uuid4().hex[:6]}",
        name="Test Source",
        kind="feed_url",
        source_type="FEED",
        access_method="HTTPS_FEED",
        source_status="ACTIVE",
        status="cleared",
        market_codes=["IN"],
        category_codes=["tops"],
    )
    sync_db_session.add(source)

    perm = CatalogSourcePermission(
        source_id=source.id,
        permission_code=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
        permission_status=CatalogPermissionStatus.GRANTED.value,
        granted_by="founder@fashx.internal",
        effective_at=datetime.now(UTC),
    )
    sync_db_session.add(perm)

    import hashlib

    img_sha256 = hashlib.sha256(sample_image_bytes).hexdigest()

    asset = CatalogImageAsset(
        id=uuid4(),
        source_id=source.id,
        merchant_id=merchant.id,
        source_product_id=f"SKU-{uuid4().hex[:6]}",
        status=ImageAssetStatus.ACTIVE.value,
        original_sha256=img_sha256,
        normalized_sha256=img_sha256,
    )
    sync_db_session.add(asset)
    sync_db_session.commit()

    return merchant, asset
