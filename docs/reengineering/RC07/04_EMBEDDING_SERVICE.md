# RC07 — Embedding Service Specification

## 1. Objective
Introduce `EmbeddingService` as a centralized multimodal orchestration layer that enforces input byte validation, batch processing, vector integrity checks, and model key encapsulation.

## 2. Service Architecture
- **Module**: `backend/fashx/catalog/embeddings/service.py`
- **Result Object**:
```python
@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model_id: str
    model_version: str
    dim: int

    @property
    def model_key(self) -> str:
        return f"{self.model_id}:{self.model_version}"
```

## 3. Core Capabilities
- `embed_image(image_bytes: bytes, validate_input: bool = True) -> EmbeddingResult`
  - Runs `validate_image_bytes(image_bytes)` before passing to provider.
  - Verifies output vector has 512 dimensions, non-zero norm, and no NaN/Inf.
- `embed_images_batch(images: Sequence[bytes], validate_input: bool = True) -> list[EmbeddingResult]`
  - Validates full batch, checks returned vector count matches input length.
- `embed_text(text: str) -> EmbeddingResult`
  - Rejects empty or whitespace-only queries.
  - Embeds query into 512-dim multimodal space and validates vector.
- `embed_texts_batch(texts: Sequence[str]) -> list[EmbeddingResult]`
  - Validates and embeds query batches.

## 4. Verification
Unit test `tests/unit/test_rc07_embedding_service.py` verifies:
- Single image embedding and normalization.
- Corrupt/empty image byte rejection.
- Text embedding with empty string rejection.
- Batch image and batch text processing.
