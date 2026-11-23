from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog_embeddings import (
    EmbeddingBatchRecord,
    EmbeddingJobRecord,
    ProductImageEmbeddingRecord,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.embeddings.preprocessing import PreprocessingConfig, preprocess_image_bytes
from fashx.catalog.embeddings.registry import EmbeddingModelRegistry
from fashx.catalog.embeddings.validation import validate_vector_invariants

logger = logging.getLogger(__name__)


class BatchEmbeddingProcessor:
    """Processes batches of catalog images for high-throughput embedding generation."""

    def __init__(
        self,
        registry: EmbeddingModelRegistry | None = None,
        default_batch_size: int = 32,
    ) -> None:
        self.registry = registry or EmbeddingModelRegistry.get_instance()
        self.default_batch_size = default_batch_size
        self.preprocessing_config = PreprocessingConfig()

    def generate_batch_key(
        self,
        model_id: str,
        model_version: str,
        asset_ids: Sequence[UUID],
    ) -> str:
        """Derive deterministic batch idempotency key."""
        sorted_ids = ",".join(str(i) for i in sorted(asset_ids))
        raw = f"{model_id}:{model_version}:{sorted_ids}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def process_batch(
        self,
        session: Session,
        items: Sequence[tuple[CatalogImageAsset, bytes, UUID]],  # (asset, bytes, product_id)
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
    ) -> EmbeddingBatchRecord:
        """Process a batch of images into embeddings with durable job tracking."""
        if not items:
            raise ValueError("Cannot process empty batch")

        asset_ids = [item[0].id for item in items]
        batch_key = self.generate_batch_key(model_id, model_version, asset_ids)

        # Check existing batch
        existing_batch = session.scalars(
            select(EmbeddingBatchRecord).where(EmbeddingBatchRecord.batch_key == batch_key)
        ).first()

        if existing_batch is not None and existing_batch.status == "COMPLETED":
            return existing_batch

        batch = existing_batch or EmbeddingBatchRecord(
            batch_key=batch_key,
            model_id=model_id,
            model_version=model_version,
            total_items=len(items),
            succeeded_items=0,
            failed_items=0,
            status="IN_PROGRESS",
        )
        if existing_batch is None:
            session.add(batch)
            session.flush()

        adapter = self.registry.get_adapter(model_id, model_version)

        preprocessed_list: list[bytes] = []
        valid_indices: list[int] = []

        # 1. Preprocessing pass
        for idx, (asset, img_bytes, _) in enumerate(items):
            job = EmbeddingJobRecord(
                batch_id=batch.id,
                image_asset_id=asset.id,
                model_id=model_id,
                model_version=model_version,
                status="IN_PROGRESS",
                attempts=1,
            )
            session.add(job)
            session.flush()

            try:
                if asset.status != ImageAssetStatus.ACTIVE:
                    raise ValueError(f"Asset status is '{asset.status}', must be ACTIVE")

                preprocessed = preprocess_image_bytes(
                    img_bytes, config=self.preprocessing_config, output_format="JPEG"
                )
                preprocessed_list.append(preprocessed)
                valid_indices.append(idx)
            except Exception as exc:
                job.status = "FAILED"
                job.last_error = str(exc)
                job.completed_at = datetime.now(UTC)
                batch.failed_items += 1
                logger.error("Preprocessing failed for asset %s: %s", asset.id, exc)

        # 2. Batched model inference
        if preprocessed_list:
            try:
                vectors = adapter.embed_batch(preprocessed_list)
                if len(vectors) != len(preprocessed_list):
                    raise RuntimeError(
                        f"Expected {len(preprocessed_list)} vectors, got {len(vectors)}"
                    )

                for vec_idx, item_idx in enumerate(valid_indices):
                    asset, _, product_id = items[item_idx]
                    vec = vectors[vec_idx]
                    validate_vector_invariants(vec, expected_dim=adapter.dimension)

                    prep_sha256 = hashlib.sha256(preprocessed_list[vec_idx]).hexdigest()

                    # Upsert embedding record
                    existing = session.scalars(
                        select(ProductImageEmbeddingRecord).where(
                            ProductImageEmbeddingRecord.image_asset_id == asset.id,
                            ProductImageEmbeddingRecord.model_id == model_id,
                            ProductImageEmbeddingRecord.model_version == model_version,
                        )
                    ).first()

                    if existing is None:
                        rec = ProductImageEmbeddingRecord(
                            image_asset_id=asset.id,
                            product_id=product_id,
                            merchant_id=asset.merchant_id,
                            model_id=model_id,
                            model_version=model_version,
                            embedding=vec,
                            image_sha256=prep_sha256,
                            status="ACTIVE",
                            is_active=True,
                        )
                        session.add(rec)
                    else:
                        existing.embedding = vec
                        existing.image_sha256 = prep_sha256
                        existing.is_active = True

                    batch.succeeded_items += 1

            except Exception as exc:
                logger.error("Batch inference failed: %s", exc)
                batch.failed_items += len(valid_indices)

        batch.status = "COMPLETED" if batch.failed_items == 0 else "PARTIALLY_FAILED"
        batch.completed_at = datetime.now(UTC)
        session.flush()
        return batch


__all__ = ["BatchEmbeddingProcessor"]
