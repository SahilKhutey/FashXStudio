from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Sequence

from fashx.catalog.embeddings.base import EmbeddingModelMetadata, ImageEmbeddingAdapter
from fashx.catalog.embeddings.preprocessing import PreprocessingConfig, preprocess_image
from fashx.catalog.embeddings.validation import validate_vector_invariants


class MockViTB32Adapter(ImageEmbeddingAdapter):
    """Deterministic, fast mock adapter simulating OpenCLIP ViT-B/32 (512-dim).

    Produces strictly reproducible, L2-normalized 512-dimensional vectors
    derived from SHA-256 and MD5 hashing of the preprocessed image bytes.
    Suitable for fast unit/integration testing and CI without heavy ML frameworks.
    """

    def __init__(
        self,
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
        dimension: int = 512,
    ) -> None:
        self._model_id = model_id
        self._model_version = model_version
        self._dimension = dimension
        self._metadata = EmbeddingModelMetadata(
            model_id=model_id,
            model_version=model_version,
            dimension=dimension,
            architecture="Mock ViT-B/32",
            framework="deterministic_mock",
            description="Mock adapter for testing",
        )
        self._preprocessing_config = PreprocessingConfig()

    @property
    def metadata(self) -> EmbeddingModelMetadata:
        return self._metadata

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector_from_bytes(self, image_bytes: bytes) -> list[float]:
        """Generate deterministic pseudo-random unit vector from byte content."""
        # Validate and preprocess image bytes first
        preprocess_image(image_bytes, self._preprocessing_config)

        # Hash input to derive deterministic floats
        raw_values: list[float] = []
        seed = hashlib.sha256(image_bytes).digest()

        chunk_idx = 0
        while len(raw_values) < self._dimension:
            h = hashlib.sha256(seed + struct.pack(">I", chunk_idx)).digest()
            chunk_idx += 1
            # Unpack 8 32-bit floats
            for i in range(0, 32, 4):
                if len(raw_values) >= self._dimension:
                    break
                int_val = struct.unpack(">i", h[i : i + 4])[0]
                # Scale to [-1.0, 1.0]
                val = (int_val / 2147483648.0)
                raw_values.append(val)

        # L2-normalize
        norm = math.sqrt(sum(x * x for x in raw_values))
        if norm == 0.0 or math.isclose(norm, 0.0, abs_tol=1e-7):
            raw_values[0] = 1.0
            norm = 1.0

        normalized = [x / norm for x in raw_values]
        validate_vector_invariants(normalized, expected_dim=self._dimension)
        return normalized

    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Embed a single image into an L2-normalized vector."""
        return self._generate_vector_from_bytes(image_bytes)

    def embed_batch(self, images: Sequence[bytes]) -> list[list[float]]:
        """Embed a sequence of images into vectors preserving input order."""
        return [self._generate_vector_from_bytes(b) for b in images]

    # Multimodal / text compatibility
    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        return self.embed_batch(images)

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for t in texts:
            b = t.encode("utf-8")
            raw_values: list[float] = []
            seed = hashlib.sha256(b).digest()
            chunk_idx = 0
            while len(raw_values) < self._dimension:
                h = hashlib.sha256(seed + struct.pack(">I", chunk_idx)).digest()
                chunk_idx += 1
                for i in range(0, 32, 4):
                    if len(raw_values) >= self._dimension:
                        break
                    int_val = struct.unpack(">i", h[i : i + 4])[0]
                    raw_values.append(int_val / 2147483648.0)
            norm = math.sqrt(sum(x * x for x in raw_values))
            if norm == 0.0 or math.isclose(norm, 0.0, abs_tol=1e-7):
                raw_values[0] = 1.0
                norm = 1.0
            results.append([x / norm for x in raw_values])
        return results


__all__ = ["MockViTB32Adapter"]
