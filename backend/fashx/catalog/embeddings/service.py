from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass

from fashx.catalog.embeddings.ports import ImageTextEmbedder, validate_embedding_vector
from fashx.catalog.images.validator import validate_image_bytes


@dataclass(frozen=True)
class EmbeddingResult:
    """Validated multimodal embedding vector and its model provenance."""

    vector: list[float]
    model_id: str
    model_version: str
    dim: int

    @property
    def model_key(self) -> str:
        """Standardized serialized model identifier '<model_id>:<model_version>'."""
        return f"{self.model_id}:{self.model_version}"


class EmbeddingService:
    """Multimodal embedding service orchestrating model execution, input/output validation."""

    def __init__(self, provider: ImageTextEmbedder) -> None:
        self.provider = provider
        self.model_id = provider.model_id
        self.model_version = provider.model_version
        self.dim = provider.dim

    @property
    def model_key(self) -> str:
        return f"{self.model_id}:{self.model_version}"

    def embed_image(self, image_bytes: bytes, validate_input: bool = True) -> EmbeddingResult:
        """Validate input image bytes, generate 512-dim normalized vector, and verify validity."""
        if validate_input:
            validate_image_bytes(image_bytes)

        vectors = self.provider.embed_images([image_bytes])
        if not vectors:
            raise RuntimeError("Embedder provider returned empty vector list for image")

        vec = vectors[0]
        validate_embedding_vector(vec, expected_dim=self.dim)
        return EmbeddingResult(
            vector=vec,
            model_id=self.model_id,
            model_version=self.model_version,
            dim=self.dim,
        )

    def embed_images_batch(
        self,
        images: Sequence[bytes],
        validate_input: bool = True,
    ) -> list[EmbeddingResult]:
        """Validate and embed a batch of image byte buffers."""
        if not images:
            return []

        if validate_input:
            for i, b in enumerate(images):
                try:
                    validate_image_bytes(b)
                except ValueError as exc:
                    raise ValueError(f"Image at index {i} failed validation: {exc}") from exc

        vectors = self.provider.embed_images(list(images))
        if len(vectors) != len(images):
            raise RuntimeError(
                f"Embedder returned {len(vectors)} vectors for {len(images)} input images"
            )

        results: list[EmbeddingResult] = []
        for vec in vectors:
            validate_embedding_vector(vec, expected_dim=self.dim)
            results.append(
                EmbeddingResult(
                    vector=vec,
                    model_id=self.model_id,
                    model_version=self.model_version,
                    dim=self.dim,
                )
            )
        return results

    def embed_text(self, text: str) -> EmbeddingResult:
        """Validate input text query, generate semantic embedding, and verify output vector."""
        clean = text.strip()
        if not clean:
            raise ValueError("Cannot embed empty or whitespace-only text")

        vectors = self.provider.embed_text([clean])
        if not vectors:
            raise RuntimeError("Embedder provider returned empty vector list for text")

        vec = vectors[0]
        validate_embedding_vector(vec, expected_dim=self.dim)
        return EmbeddingResult(
            vector=vec,
            model_id=self.model_id,
            model_version=self.model_version,
            dim=self.dim,
        )

    def embed_texts_batch(self, texts: Sequence[str]) -> list[EmbeddingResult]:
        """Validate and embed a batch of text queries."""
        if not texts:
            return []

        cleaned: list[str] = []
        for i, t in enumerate(texts):
            clean = t.strip()
            if not clean:
                raise ValueError(f"Text at index {i} is empty or whitespace-only")
            cleaned.append(clean)

        vectors = self.provider.embed_text(cleaned)
        if len(vectors) != len(cleaned):
            raise RuntimeError(
                f"Embedder returned {len(vectors)} vectors for {len(cleaned)} input texts"
            )

        results: list[EmbeddingResult] = []
        for vec in vectors:
            validate_embedding_vector(vec, expected_dim=self.dim)
            results.append(
                EmbeddingResult(
                    vector=vec,
                    model_id=self.model_id,
                    model_version=self.model_version,
                    dim=self.dim,
                )
            )
        return results


def get_default_embedder() -> ImageTextEmbedder:
    """Instantiate appropriate embedder based on operational environment."""
    env = os.getenv("ENV", "dev").lower()
    if env == "production":
        from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder

        return MarqoFashionClipEmbedder()

    from fashx.catalog.embeddings.fake import FakeEmbedder

    return FakeEmbedder()
