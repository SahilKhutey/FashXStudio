from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog_search import ProductTextEmbeddingRecord
from fashx.catalog.embeddings.registry import EmbeddingModelRegistry
from fashx.catalog.embeddings.retrieval import compute_cosine_similarity
from fashx.catalog.embeddings.validation import validate_vector_invariants

logger = logging.getLogger(__name__)


def execute_semantic_search(
    session: Session,
    query_text: str,
    model_id: str = "openclip_vit_b32",
    model_version: str = "v1",
    limit: int = 50,
    min_similarity: float = 0.50,
) -> list[tuple[UUID, float]]:
    """Execute natural language semantic search using joint multimodal text embeddings."""
    if not query_text or not query_text.strip():
        return []

    registry = EmbeddingModelRegistry.get_instance()
    adapter = registry.get_adapter(model_id, model_version)

    # Encode natural language query into vector
    if hasattr(adapter, "embed_text"):
        vectors = adapter.embed_text([query_text.strip()])
        if not vectors:
            return []
        query_vector = vectors[0]
    else:
        raise RuntimeError(f"Adapter '{model_id}' does not support text embedding")

    validate_vector_invariants(query_vector, expected_dim=adapter.dimension)

    # Query candidates in product_text_embeddings
    stmt = select(ProductTextEmbeddingRecord).where(
        ProductTextEmbeddingRecord.model_id == model_id,
        ProductTextEmbeddingRecord.model_version == model_version,
        ProductTextEmbeddingRecord.status == "READY",
    )
    text_embeddings = session.scalars(stmt).all()

    scored: list[tuple[UUID, float]] = []
    for rec in text_embeddings:
        sim = compute_cosine_similarity(query_vector, rec.embedding)
        if sim >= min_similarity:
            scored.append((rec.merchant_product_id, round(sim, 4)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


__all__ = ["execute_semantic_search"]
