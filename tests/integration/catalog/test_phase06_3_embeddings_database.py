from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_embeddings import (
    EmbeddingBatchRecord,
    EmbeddingJobRecord,
    EmbeddingMigrationRecord,
    EmbeddingModelRegistryRecord,
    ProductImageEmbeddingRecord,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus


@pytest.mark.asyncio
async def test_embeddings_database_persistence_and_relationships(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verify Phase 06.3 catalog image embedding database models, relationships, and queries."""
    merchant_id = uuid4()
    source_id = uuid4()
    asset_id = uuid4()
    product_id = uuid4()

    async with session_factory() as session:
        # 1. Create merchant and source
        merchant = Merchant(
            id=merchant_id,
            name="Embedding Test Merchant",
            merchant_type="brand",
            country_code="IN",
            verification_status="VERIFIED",
        )
        session.add(merchant)

        source = CatalogSource(
            id=source_id,
            merchant_id=merchant_id,
            slug=f"src-{uuid4().hex[:6]}",
            name="Test Source",
            kind="feed_url",
            source_type="FEED",
            access_method="HTTPS_FEED",
            source_status="ACTIVE",
            status="cleared",
            market_codes=["IN"],
            category_codes=["tops"],
        )
        session.add(source)

        # 2. Create catalog image asset
        asset = CatalogImageAsset(
            id=asset_id,
            source_id=source_id,
            merchant_id=merchant_id,
            source_product_id="SKU-001",
            status=ImageAssetStatus.ACTIVE.value,
            original_sha256="orig_sha",
            normalized_sha256="norm_sha",
        )
        session.add(asset)

        # 3. Register model
        model = EmbeddingModelRegistryRecord(
            model_id="openclip_vit_b32",
            model_version="v1",
            dimension=512,
            status="APPROVED",
            architecture="ViT-B/32",
            framework="openclip",
            metadata_json={"weights": "laion2b_s34b_b79k"},
        )
        session.add(model)

        # 4. Create batch
        batch = EmbeddingBatchRecord(
            id=uuid4(),
            batch_key=f"batch-{uuid4().hex[:8]}",
            model_id="openclip_vit_b32",
            model_version="v1",
            total_items=1,
            succeeded_items=1,
            failed_items=0,
            status="COMPLETED",
        )
        session.add(batch)

        # 5. Create job linked to batch
        job = EmbeddingJobRecord(
            id=uuid4(),
            batch_id=batch.id,
            image_asset_id=asset.id,
            model_id="openclip_vit_b32",
            model_version="v1",
            status="COMPLETED",
            attempts=1,
        )
        session.add(job)

        # 6. Create embedding record
        test_vec = [1.0 / (512**0.5)] * 512
        emb_rec = ProductImageEmbeddingRecord(
            id=uuid4(),
            image_asset_id=asset.id,
            product_id=product_id,
            merchant_id=merchant_id,
            model_id="openclip_vit_b32",
            model_version="v1",
            embedding=test_vec,
            image_sha256="norm_sha",
            status="ACTIVE",
            is_active=True,
        )
        session.add(emb_rec)

        # 7. Create migration record
        migration = EmbeddingMigrationRecord(
            id=uuid4(),
            source_model_id="openclip_vit_b32",
            source_model_version="v1",
            target_model_id="openclip_vit_b32",
            target_model_version="v2",
            migration_phase="DUAL_WRITE",
            total_records=1,
            migrated_records=0,
            status="IN_PROGRESS",
        )
        session.add(migration)

        await session.commit()

    # Query back and verify
    async with session_factory() as session:
        queried_emb = await session.scalar(
            select(ProductImageEmbeddingRecord).where(
                ProductImageEmbeddingRecord.image_asset_id == asset_id
            )
        )
        assert queried_emb is not None
        assert queried_emb.model_id == "openclip_vit_b32"
        assert len(queried_emb.embedding) == 512
        assert queried_emb.is_active is True

        queried_batch = await session.scalar(
            select(EmbeddingBatchRecord).where(EmbeddingBatchRecord.id == batch.id)
        )
        assert queried_batch is not None
        assert queried_batch.total_items == 1
        assert queried_batch.status == "COMPLETED"

        queried_mig = await session.scalar(
            select(EmbeddingMigrationRecord).where(EmbeddingMigrationRecord.id == migration.id)
        )
        assert queried_mig is not None
        assert queried_mig.migration_phase == "DUAL_WRITE"
