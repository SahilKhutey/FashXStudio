from __future__ import annotations

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
from fashx.catalog.embeddings.ports import (
    ImageEmbedder,
    ImageTextEmbedder,
    validate_embedding_vector,
)
from fashx.catalog.embeddings.service import EmbeddingResult, EmbeddingService, get_default_embedder

__all__ = [
    "FakeEmbedder",
    "ImageEmbedder",
    "ImageTextEmbedder",
    "MarqoFashionClipEmbedder",
    "EmbeddingResult",
    "EmbeddingService",
    "get_default_embedder",
    "validate_embedding_vector",
]
