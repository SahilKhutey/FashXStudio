from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from database.models.catalog import Merchant
from database.models.catalog_embeddings import (
    EmbeddingJobRecord,
    EmbeddingModelRegistryRecord,
    ProductImageEmbeddingRecord,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.embeddings import (
    EmbeddingResult,
    EmbeddingService,
    FakeEmbedder,
    ImageEmbedder,
    ImageTextEmbedder,
    get_default_embedder,
    validate_embedding_vector,
)
from fashx.catalog.embeddings.jobs.batch import BatchEmbeddingProcessor
from fashx.catalog.embeddings.jobs.retry import EmbeddingRetryHandler, EmbeddingRetryPolicy
from fashx.catalog.embeddings.migration import ModelMigrationManager
from fashx.catalog.embeddings.preprocessing import PreprocessingError


def test_emb_019_blue_green_migration_cutover(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-019: Blue/green model migration enables dual-model coexistence and atomic cutover."""
    merchant, asset = setup_catalog_image_asset
    product_id = uuid4()

    # Pre-register green model
    green_meta = EmbeddingModelRegistryRecord(
        model_id="openclip_vit_b32",
        model_version="v2",
        dimension=512,
        status="APPROVED",
        architecture="ViT-B/32",
        framework="openclip",
        metadata_json={},
    )
    sync_db_session.add(green_meta)

    # Blue vector (v1): active
    vec_blue = [0.0] * 512
    vec_blue[0] = 1.0
    rec_blue = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=vec_blue,
        image_sha256="sha_v1",
        status="ACTIVE",
        is_active=True,
    )
    # Green vector (v2): inactive dual-write
    vec_green = [0.0] * 512
    vec_green[1] = 1.0
    rec_green = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v2",
        embedding=vec_green,
        image_sha256="sha_v2",
        status="ACTIVE",
        is_active=False,
    )
    sync_db_session.add_all([rec_blue, rec_green])
    sync_db_session.commit()

    manager = ModelMigrationManager()
    migration = manager.start_migration(
        session=sync_db_session,
        source_model_id="openclip_vit_b32",
        source_model_version="v1",
        target_model_id="openclip_vit_b32",
        target_model_version="v2",
    )
    assert migration.status == "IN_PROGRESS"
    assert migration.migration_phase == "DUAL_WRITE"

    # Execute atomic cutover
    manager.execute_cutover(sync_db_session, migration.id)

    sync_db_session.refresh(rec_blue)
    sync_db_session.refresh(rec_green)
    assert rec_blue.is_active is False
    assert rec_green.is_active is True
    assert migration.status == "COMPLETED"


def test_emb_020_canary_rollback(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
) -> None:
    """Verify EMB-020: Canary rollback restores source model vectors as active."""
    merchant, asset = setup_catalog_image_asset
    product_id = uuid4()

    # Pre-register green model
    green_meta = EmbeddingModelRegistryRecord(
        model_id="openclip_vit_b32",
        model_version="v2",
        dimension=512,
        status="APPROVED",
        architecture="ViT-B/32",
        framework="openclip",
        metadata_json={},
    )
    sync_db_session.add(green_meta)

    rec_blue = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v1",
        embedding=[1.0] + [0.0] * 511,
        image_sha256="sha_v1",
        status="ACTIVE",
        is_active=True,
    )
    rec_green = ProductImageEmbeddingRecord(
        image_asset_id=asset.id,
        product_id=product_id,
        merchant_id=merchant.id,
        model_id="openclip_vit_b32",
        model_version="v2",
        embedding=[0.0, 1.0] + [0.0] * 510,
        image_sha256="sha_v2",
        status="ACTIVE",
        is_active=False,
    )
    sync_db_session.add_all([rec_blue, rec_green])
    sync_db_session.commit()

    manager = ModelMigrationManager()
    migration = manager.start_migration(
        sync_db_session, "openclip_vit_b32", "v1", "openclip_vit_b32", "v2"
    )
    manager.execute_cutover(sync_db_session, migration.id)

    # Rollback
    manager.rollback(sync_db_session, migration.id)
    sync_db_session.refresh(rec_blue)
    sync_db_session.refresh(rec_green)

    assert rec_blue.is_active is True
    assert rec_green.is_active is False
    assert migration.status == "ROLLED_BACK"


def test_emb_021_batch_processing(
    sync_db_session: Session,
    setup_catalog_image_asset: tuple[Merchant, CatalogImageAsset],
    sample_image_bytes: bytes,
) -> None:
    """Verify EMB-021: Batch processing creates batch records and jobs in order."""
    merchant, asset = setup_catalog_image_asset
    product1 = uuid4()
    product2 = uuid4()

    asset2 = CatalogImageAsset(
        id=uuid4(),
        source_id=asset.source_id,
        merchant_id=merchant.id,
        source_product_id="SKU-2",
        status=ImageAssetStatus.ACTIVE.value,
    )
    sync_db_session.add(asset2)
    sync_db_session.commit()

    processor = BatchEmbeddingProcessor()
    items = [
        (asset, sample_image_bytes, product1),
        (asset2, sample_image_bytes, product2),
    ]

    batch = processor.process_batch(
        session=sync_db_session,
        items=items,
        model_id="openclip_vit_b32",
        model_version="v1",
    )

    assert batch.total_items == 2
    assert batch.succeeded_items == 2
    assert batch.failed_items == 0
    assert batch.status == "COMPLETED"


def test_emb_022_retry_exponential_backoff() -> None:
    """Verify EMB-022: Exponential backoff increases delay with jitter on transient failures."""
    policy = EmbeddingRetryPolicy(base_delay=1.0, max_delay=30.0, jitter=0.1)

    delay1 = policy.compute_backoff(attempt=1)
    delay2 = policy.compute_backoff(attempt=2)
    delay3 = policy.compute_backoff(attempt=3)

    assert 1.0 <= delay1 <= 1.2
    assert 2.0 <= delay2 <= 2.2
    assert 4.0 <= delay3 <= 4.2

    # Check transient vs permanent
    assert policy.is_retryable(TimeoutError("timeout"), attempt=1) is True
    assert policy.is_retryable(PreprocessingError("corrupt"), attempt=1) is False
    assert policy.is_retryable(TimeoutError("timeout"), attempt=3) is False  # Max retries reached


def test_emb_023_dead_letter_queue(sync_db_session: Session) -> None:
    """Verify EMB-023: Permanent failure records error in DLQ (embedding_jobs.status = FAILED)."""
    job = EmbeddingJobRecord(
        image_asset_id=uuid4(),
        model_id="openclip_vit_b32",
        model_version="v1",
        status="IN_PROGRESS",
        attempts=0,
    )
    sync_db_session.add(job)
    sync_db_session.commit()

    handler = EmbeddingRetryHandler()
    updated = handler.handle_failure(
        session=sync_db_session,
        job_id=job.id,
        exc=PreprocessingError("Non-recoverable corrupt file"),
    )

    assert updated.status == "FAILED"
    assert updated.attempts == 1
    assert "PreprocessingError" in updated.last_error


def test_emb_024_backward_compatibility() -> None:
    """Verify EMB-024: Legacy FakeEmbedder, ImageTextEmbedder, and EmbeddingService imports succeed."""
    embedder = FakeEmbedder()
    assert isinstance(embedder, ImageTextEmbedder)
    assert isinstance(embedder, ImageEmbedder)
    assert embedder.dim == 512

    service = EmbeddingService(embedder)
    text_res = service.embed_text("navy blue cotton shirt")
    assert isinstance(text_res, EmbeddingResult)
    assert len(text_res.vector) == 512
    validate_embedding_vector(text_res.vector, expected_dim=512)

    default_emb = get_default_embedder()
    assert default_emb is not None
