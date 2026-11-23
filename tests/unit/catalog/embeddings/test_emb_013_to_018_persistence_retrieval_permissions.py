from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models.catalog import Merchant
from database.models.catalog_embeddings import ProductImageEmbeddingRecord
from database.models.catalog_image import (
    CatalogImageAsset,
    CatalogImageTakedown,
    ImageAssetStatus,
    ImageTakedownStatus,
)
from fashx.catalog.embeddings.retrieval import VisualSimilarityRetriever
from fashx.catalog.embeddings.service import (
    CatalogImageEmbeddingService,
    EmbeddingPermissionDeniedError,
)


def test_emb_013_database_persistence(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
    sample_image_bytes: bytes,
) -> None:
    """Verify EMB-013: Persists embedding vector in product_image_embeddings table."""
    _, asset = setup_catalog_image_asset
    product_id = uuid4()
    service = CatalogImageEmbeddingService()

    record = service.process_and_persist_image(
        session=sync_db_session,
        image_asset=asset,
        image_bytes=sample_image_bytes,
        product_id=product_id,
        model_id="openclip_vit_b32",
        model_version="v1",
    )

    assert record.id is not None
    assert record.image_asset_id == asset.id
    assert record.product_id == product_id
    assert len(record.embedding) == 512
    assert record.status == "ACTIVE"
    assert record.is_active is True


def test_emb_014_uniqueness_constraint(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-014: Enforces uniqueness on (image_asset_id, model_id, model_version)."""
    merchant, asset = setup_catalog_image_asset
    product_id = uuid4()
    vec = [0.0] * 512
    vec[0] = 1.0

    rec1 = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec,
        image_sha256="abc",
        status="ACTIVE",
        is_active=True,
    )
    sync_db_session.add(rec1)
    sync_db_session.commit()

    # Second insert with identical (image_asset_id, model_id, model_version)
    rec2 = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec,
        image_sha256="def",
        status="ACTIVE",
        is_active=True,
    )
    sync_db_session.add(rec2)
    with pytest.raises(IntegrityError):
        sync_db_session.commit()
    sync_db_session.rollback()


def test_emb_015_permission_enforcement(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
    sample_image_bytes: bytes,
) -> None:
    """Verify EMB-015: Skips / blocks embedding when IMAGE_AI_PROCESS is absent."""
    _, asset = setup_catalog_image_asset
    # Service configured with permission checker that rejects this merchant
    service = CatalogImageEmbeddingService(
        permission_checker=lambda merchant_id, source_id: False
    )

    with pytest.raises(EmbeddingPermissionDeniedError, match="lacks IMAGE_AI_PROCESS"):
        service.process_and_persist_image(
            session=sync_db_session,
            image_asset=asset,
            image_bytes=sample_image_bytes,
            product_id=uuid4(),
        )


def test_emb_016_content_hash_integrity(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-016: Fails if image bytes hash does not match asset record."""
    _, asset = setup_catalog_image_asset
    # Provide different image bytes whose SHA-256 does not match asset.original_sha256
    different_bytes = b"DIFFERENT_IMAGE_BYTES_THAT_DO_NOT_MATCH_SHA256"
    service = CatalogImageEmbeddingService()

    with pytest.raises(ValueError, match="does not match asset records"):
        service.process_and_persist_image(
            session=sync_db_session,
            image_asset=asset,
            image_bytes=different_bytes,
            product_id=uuid4(),
        )


def test_emb_017_nearest_neighbor_search(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-017: Cosine retrieval ranks closest vector top."""
    merchant, asset = setup_catalog_image_asset
    product1 = uuid4()
    product2 = uuid4()

    # Query vector: [1, 0, 0, ...]
    query_vec = [0.0] * 512
    query_vec[0] = 1.0

    # Vector 1: close to query ([0.99, 0.14, 0, ...])
    vec1 = [0.0] * 512
    vec1[0] = 0.99
    vec1[1] = 0.141
    # Vector 2: orthogonal/far ([0, 1, 0, ...])
    vec2 = [0.0] * 512
    vec2[1] = 1.0

    rec1 = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product1,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec1,
        image_sha256="sha1",
        status="ACTIVE",
        is_active=True,
    )
    sync_db_session.add(rec1)

    asset2 = CatalogImageAsset(
        id=uuid4(),
        source_id=asset.source_id,
        merchant_id=merchant.id,
        source_product_id="SKU-2",
        status=ImageAssetStatus.ACTIVE.value,
    )
    sync_db_session.add(asset2)
    sync_db_session.flush()

    rec2 = ProductImageEmbeddingRecord(
        image_asset_id=asset2.id,
        product_id=product2,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec2,
        image_sha256="sha2",
        status="ACTIVE",
        is_active=True,
    )
    sync_db_session.add(rec2)
    sync_db_session.commit()

    retriever = VisualSimilarityRetriever()
    results = retriever.find_similar_by_vector(
        session=sync_db_session,
        query_vector=query_vec,
        model_id="openclip_vit_b32",
        model_version="v1",
        min_similarity=0.0,
    )

    assert len(results) == 2
    assert results[0].product_id == product1
    assert results[0].similarity > results[1].similarity


def test_emb_018_visibility_and_takedown_filtering(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-018: Similarity search excludes inactive or takedown-flagged assets."""
    merchant, asset = setup_catalog_image_asset
    product1 = uuid4()
    vec = [0.0] * 512
    vec[0] = 1.0

    rec = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product1,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec,
        image_sha256="sha1",
        status="ACTIVE",
        is_active=True,
    )
    sync_db_session.add(rec)
    sync_db_session.commit()

    retriever = VisualSimilarityRetriever()

    # Initial search returns 1 result
    results = retriever.find_similar_by_vector(sync_db_session, query_vector=vec)
    assert len(results) == 1

    # 1. Flag a takedown for this source
    takedown = CatalogImageTakedown(
        id=uuid4(),
        source_id=asset.source_id,
        merchant_id=merchant.id,
        reason_code="DMCA",
        status=ImageTakedownStatus.COMPLETED.value,
    )
    sync_db_session.add(takedown)
    sync_db_session.commit()

    # After takedown, asset is excluded from search results
    takedown_results = retriever.find_similar_by_vector(sync_db_session, query_vector=vec)
    assert len(takedown_results) == 0
