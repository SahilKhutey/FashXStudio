# Fashion Image Embedding Model Adapter Contract

## 1. Specification Overview
The `ImageEmbeddingAdapter` protocol establishes the programmatic interface separating model inference implementations from FashXStudio application services, batch processors, and database layers.

Any machine learning model introduced to the catalog must satisfy this contract.

---

## 2. Protocol Definition

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class EmbeddingModelMetadata:
    """Metadata describing an approved embedding model."""
    model_id: str
    model_version: str
    dimension: int
    architecture: str
    framework: str
    weights_sha256: str | None = None

@runtime_checkable
class ImageEmbeddingAdapter(Protocol):
    """Formal protocol for vision embedding models."""

    @property
    def metadata(self) -> EmbeddingModelMetadata:
        """Return model metadata."""
        ...

    @property
    def model_id(self) -> str:
        """Unique model family identifier (e.g., 'openclip_vit_b32')."""
        ...

    @property
    def model_version(self) -> str:
        """Version string for the weights checkpoint (e.g., 'v1')."""
        ...

    @property
    def dimension(self) -> int:
        """Fixed dimensionality of generated output vectors (e.g., 512)."""
        ...

    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Generate an L2-normalized float embedding vector for a single image.
        
        Args:
            image_bytes: Raw binary image data (JPEG, PNG, WebP).
            
        Returns:
            List of 512 float values with unit Euclidean norm.
            
        Raises:
            ValueError: If input image is corrupted or invalid.
            RuntimeError: If model inference fails.
        """
        ...

    def embed_batch(self, images: list[bytes]) -> list[list[float]]:
        """Generate L2-normalized embeddings for a batch of images.
        
        Args:
            images: List of raw binary image data.
            
        Returns:
            List of embedding vectors, strictly preserving input ordering.
            
        Raises:
            ValueError: If any input image is corrupted.
            RuntimeError: If model inference fails.
        """
        ...
```

---

## 3. Invariants and Guarantees
1. **L2 Unit Normalization**: All returned vectors must satisfy:
   $$\sqrt{\sum_{i=1}^{d} v_i^2} = 1.0 \pm 10^{-5}$$
2. **Deterministic Output**: Identical input bytes passed to the same model checkpoint must yield identical vectors within IEEE 754 float32 precision limits.
3. **Finite Floating-Point Values**: Vectors must never contain `NaN`, `+Inf`, or `-Inf`.
4. **Order Preservation**: In batch calls, the output vector at index $i$ corresponds strictly to the image at index $i$.
5. **No Out-of-Band Network Calls**: Adapter implementations must execute locally without making external HTTP requests.
