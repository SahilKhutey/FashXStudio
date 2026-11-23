from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog_embeddings import ProductImageEmbeddingRecord
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.embeddings.retrieval import VisualSimilarityRetriever

logger = logging.getLogger(__name__)


def execute_visual_search(
    session: Session,
    query_image_asset_id: UUID,
    model_id: str = "openclip_vit_b32",
    model_version: str = "v1",
    limit: int = 50,
    min_similarity: float = 0.50,
) -> list[tuple[UUID, float]]:
    """Execute visual similarity search using a reference image asset."""
    # 1. Verify query image asset exists and is authorized/active
    asset = session.get(CatalogImageAsset, query_image_asset_id)
    if asset is None:
        raise KeyError(f"Query image asset {query_image_asset_id} not found")

    if asset.status != ImageAssetStatus.ACTIVE.value and asset.status != "ACTIVE":
        raise PermissionError(f"Query image asset is not authorized for search (status: {asset.status})")

    # 2. Retrieve nearest neighbor images
    retriever = VisualSimilarityRetriever(default_limit=limit, default_min_similarity=min_similarity)
    results = retriever.find_similar_by_image(
        session=session,
        image_asset_id=query_image_asset_id,
        model_id=model_id,
        model_version=model_version,
        limit=limit,
        min_similarity=min_similarity,
        exclude_same_product=True,
    )

    # 3. Map image results to merchant products
    if not results:
        return []

    asset_ids = [r.image_asset_id for r in results]
    # Query product_id / merchant_product_id
    stmt = select(ProductImageEmbeddingRecord.image_asset_id, ProductImageEmbeddingRecord.product_id).where(
        ProductImageEmbeddingRecord.image_asset_id.in_(asset_ids)
    )
    mapping = dict(session.execute(stmt).all())

    scored_candidates: list[tuple[UUID, float]] = []
    for r in results:
        prod_id = mapping.get(r.image_asset_id, r.product_id)
        # Check if product is merchant_product or canonical
        scored_candidates.append((prod_id, r.similarity))

    return scored_candidates[:limit]


__all__ = ["execute_visual_search"]
