from __future__ import annotations

import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class ImageTextEmbedder(Protocol):
    """Protocol for multimodal fashion image and text embedding models."""

    model_id: str
    dim: int

    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        ...

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        ...


# Reconciled alias for backward compatibility with existing ImageEmbedder callers
ImageEmbedder = ImageTextEmbedder


def validate_embedding_vector(vector: list[float], expected_dim: int = 512) -> None:
    """Validate that vector has correct dimension, finite values, and non-zero norm."""
    if len(vector) != expected_dim:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dim}, got {len(vector)}"
        )
    if not all(math.isfinite(x) for x in vector):
        raise ValueError("Embedding vector contains non-finite values (NaN or Inf)")
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0 or math.isclose(norm, 0.0, abs_tol=1e-7):
        raise ValueError("Embedding vector has zero norm")
