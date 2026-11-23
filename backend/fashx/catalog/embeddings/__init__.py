from __future__ import annotations

from fashx.catalog.embeddings.base import (
    EmbeddingModelMetadata,
    ImageEmbedder,
    ImageEmbeddingAdapter,
    ImageTextEmbedder,
)
from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.jobs.batch import BatchEmbeddingProcessor
from fashx.catalog.embeddings.jobs.retry import EmbeddingRetryHandler, EmbeddingRetryPolicy
from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
from fashx.catalog.embeddings.migration import ModelMigrationError, ModelMigrationManager
from fashx.catalog.embeddings.models.mock_adapter import MockViTB32Adapter
from fashx.catalog.embeddings.models.openclip_adapter import OpenCLIPViTB32Adapter
from fashx.catalog.embeddings.ports import validate_embedding_vector
from fashx.catalog.embeddings.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    preprocess_image,
    preprocess_image_bytes,
)
from fashx.catalog.embeddings.registry import EmbeddingModelRegistry
from fashx.catalog.embeddings.retrieval import (
    SimilaritySearchResult,
    VisualSimilarityRetriever,
    compute_cosine_similarity,
)
from fashx.catalog.embeddings.service import (
    CatalogImageEmbeddingService,
    EmbeddingPermissionDeniedError,
    EmbeddingResult,
    EmbeddingService,
    get_default_embedder,
)
from fashx.catalog.embeddings.validation import validate_vector_invariants

__all__ = [
    # Legacy exports
    "FakeEmbedder",
    "ImageEmbedder",
    "ImageTextEmbedder",
    "MarqoFashionClipEmbedder",
    "EmbeddingResult",
    "EmbeddingService",
    "get_default_embedder",
    "validate_embedding_vector",
    # Phase 06.3 exports
    "EmbeddingModelMetadata",
    "ImageEmbeddingAdapter",
    "EmbeddingModelRegistry",
    "PreprocessingConfig",
    "PreprocessingError",
    "preprocess_image",
    "preprocess_image_bytes",
    "validate_vector_invariants",
    "CatalogImageEmbeddingService",
    "EmbeddingPermissionDeniedError",
    "VisualSimilarityRetriever",
    "SimilaritySearchResult",
    "compute_cosine_similarity",
    "ModelMigrationManager",
    "ModelMigrationError",
    "BatchEmbeddingProcessor",
    "EmbeddingRetryHandler",
    "EmbeddingRetryPolicy",
    "OpenCLIPViTB32Adapter",
    "MockViTB32Adapter",
]
