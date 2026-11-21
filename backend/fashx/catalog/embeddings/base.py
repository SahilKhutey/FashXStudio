from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from fashx.catalog.embeddings.ports import ImageEmbedder, ImageTextEmbedder


@dataclass(frozen=True)
class EmbeddingModelMetadata:
    """Metadata describing an approved embedding model."""

    model_id: str
    model_version: str
    dimension: int
    architecture: str
    framework: str
    weights_sha256: str | None = None
    description: str = ""


@runtime_checkable
class ImageEmbeddingAdapter(Protocol):
    """Protocol for fashion image embedding adapters."""

    @property
    def metadata(self) -> EmbeddingModelMetadata:
        """Return model metadata."""
        ...

    @property
    def model_id(self) -> str:
        """Model identifier (e.g., 'openclip_vit_b32')."""
        ...

    @property
    def model_version(self) -> str:
        """Model checkpoint version (e.g., 'v1')."""
        ...

    @property
    def dimension(self) -> int:
        """Output embedding vector dimensionality (e.g., 512)."""
        ...

    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Generate an L2-normalized float embedding vector for an image."""
        ...

    def embed_batch(self, images: list[bytes]) -> list[list[float]]:
        """Generate L2-normalized embedding vectors for a batch of images."""
        ...


__all__ = [
    "EmbeddingModelMetadata",
    "ImageEmbeddingAdapter",
    "ImageEmbedder",
    "ImageTextEmbedder",
]
