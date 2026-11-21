from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog_embeddings import ProductImageEmbeddingRecord
from database.models.catalog_image import (
    CatalogImageAsset,
    CatalogImageTakedown,
    ImageAssetStatus,
    ImageTakedownStatus,
)
from fashx.catalog.embeddings.validation import validate_vector_invariants


@dataclass(frozen=True)
class SimilaritySearchResult:
    """Individual visual similarity match result."""

    product_id: UUID
    image_asset_id: UUID
    merchant_id: UUID
    similarity: float
    cosine_distance: float
    model_id: str
    model_version: str


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Assumes unit-normalized vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    return max(-1.0, min(1.0, dot))


class VisualSimilarityRetriever:
    """Retrieves visually similar catalog items using pgvector or in-memory vector search."""

    def __init__(self, default_limit: int = 20, default_min_similarity: float = 0.60) -> None:
        self.default_limit = default_limit
        self.default_min_similarity = default_min_similarity

    def find_similar_by_vector(
        self,
        session: Session,
        query_vector: list[float],
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
        limit: int | None = None,
        min_similarity: float | None = None,
        filter_merchant_ids: list[UUID] | None = None,
        filter_product_ids: list[UUID] | None = None,
        exclude_product_ids: list[UUID] | None = None,
        exclude_image_asset_ids: list[UUID] | None = None,
    ) -> list[SimilaritySearchResult]:
        """Find nearest-neighbor catalog items for a query embedding vector."""
        lim = limit or self.default_limit
        min_sim = min_similarity if min_similarity is not None else self.default_min_similarity
        validate_vector_invariants(query_vector)

        # 1. Fetch active takedown scopes to exclude
        active_takedowns_stmt = select(CatalogImageTakedown).where(
            CatalogImageTakedown.status.in_([
                ImageTakedownStatus.PROCESSING.value,
                ImageTakedownStatus.COMPLETED.value,
            ])
        )
        takedowns = session.scalars(active_takedowns_stmt).all()
        takedown_merchants = {t.merchant_id for t in takedowns if t.merchant_id is not None}
        takedown_sources = {t.source_id for t in takedowns if t.source_id is not None}

        # 2. Build candidate query joining with image asset
        stmt = (
            select(ProductImageEmbeddingRecord, CatalogImageAsset)
            .join(CatalogImageAsset, ProductImageEmbeddingRecord.image_asset_id == CatalogImageAsset.id)
            .where(
                ProductImageEmbeddingRecord.is_active == True,  # noqa: E712
                ProductImageEmbeddingRecord.model_id == model_id,
                ProductImageEmbeddingRecord.model_version == model_version,
                CatalogImageAsset.status == ImageAssetStatus.ACTIVE,
            )
        )

        if filter_merchant_ids:
            stmt = stmt.where(ProductImageEmbeddingRecord.merchant_id.in_(filter_merchant_ids))
        if filter_product_ids:
            stmt = stmt.where(ProductImageEmbeddingRecord.product_id.in_(filter_product_ids))
        if exclude_product_ids:
            stmt = stmt.where(ProductImageEmbeddingRecord.product_id.notin_(exclude_product_ids))
        if exclude_image_asset_ids:
            stmt = stmt.where(ProductImageEmbeddingRecord.image_asset_id.notin_(exclude_image_asset_ids))

        candidates = session.execute(stmt).all()

        scored_results: list[SimilaritySearchResult] = []
        for embedding_rec, asset_rec in candidates:
            # Exclude takedowns
            if asset_rec.merchant_id in takedown_merchants or asset_rec.source_id in takedown_sources:
                continue

            sim = compute_cosine_similarity(query_vector, embedding_rec.embedding)
            if sim < min_sim:
                continue

            dist = 1.0 - sim
            scored_results.append(
                SimilaritySearchResult(
                    product_id=embedding_rec.product_id,
                    image_asset_id=embedding_rec.image_asset_id,
                    merchant_id=embedding_rec.merchant_id,
                    similarity=round(sim, 4),
                    cosine_distance=round(dist, 4),
                    model_id=embedding_rec.model_id,
                    model_version=embedding_rec.model_version,
                )
            )

        # Sort descending by similarity
        scored_results.sort(key=lambda r: r.similarity, reverse=True)
        return scored_results[:lim]

    def find_similar_by_image(
        self,
        session: Session,
        image_asset_id: UUID,
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
        limit: int | None = None,
        min_similarity: float | None = None,
        filter_merchant_ids: list[UUID] | None = None,
        exclude_same_product: bool = True,
    ) -> list[SimilaritySearchResult]:
        """Find similar catalog items using an existing catalog image asset as reference."""
        stmt = select(ProductImageEmbeddingRecord).where(
            ProductImageEmbeddingRecord.image_asset_id == image_asset_id,
            ProductImageEmbeddingRecord.model_id == model_id,
            ProductImageEmbeddingRecord.model_version == model_version,
        )
        source_rec = session.scalars(stmt).first()
        if source_rec is None:
            raise KeyError(
                f"No embedding found for image asset {image_asset_id} with model {model_id}:{model_version}"
            )

        exclude_products = [source_rec.product_id] if exclude_same_product else None
        exclude_images = [image_asset_id]

        return self.find_similar_by_vector(
            session=session,
            query_vector=source_rec.embedding,
            model_id=model_id,
            model_version=model_version,
            limit=limit,
            min_similarity=min_similarity,
            filter_merchant_ids=filter_merchant_ids,
            exclude_product_ids=exclude_products,
            exclude_image_asset_ids=exclude_images,
        )


__all__ = [
    "SimilaritySearchResult",
    "VisualSimilarityRetriever",
    "compute_cosine_similarity",
]
