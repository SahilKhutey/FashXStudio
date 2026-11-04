# RC07 — Multimodal Embedding Provider Protocol & Pinning

## 1. Objective
Establish an explicit, versioned protocol for multimodal embedding models, pin production and mock model identifiers, and guarantee environment-level safeguards against synthetic vectors reaching production ranking.

## 2. Protocol Definition
- **Module**: `backend/fashx/catalog/embeddings/ports.py`
```python
@runtime_checkable
class ImageTextEmbedder(Protocol):
    """Protocol for multimodal fashion image and text embedding models."""

    model_id: str
    model_version: str
    dim: int

    def embed_images(self, images: list[bytes]) -> list[list[float]]: ...
    def embed_text(self, texts: list[str]) -> list[list[float]]: ...
```

## 3. Provider Implementations
### A. Production Provider (`MarqoFashionClipEmbedder`)
- **Module**: `backend/fashx/catalog/embeddings/marqo_fashionclip.py`
- **Model ID**: `Marqo/marqo-fashionCLIP`
- **Model Version**: `2026.1`
- **Embedding Dimensions**: 512
- **Pretrained Weights**: `hf-hub:Marqo/marqo-fashionCLIP`
- **Normalization**: Unit L2 normalization (`f / f.norm(dim=-1, keepdim=True)`).

### B. Development & Test Provider (`FakeEmbedder`)
- **Module**: `backend/fashx/catalog/embeddings/fake.py`
- **Model ID**: `mock-fake-512`
- **Model Version**: `mock-v1`
- **Embedding Dimensions**: 512
- **Production Guard**: Raises `RuntimeError` if `ENV == "production"`.

## 4. Verification
Unit test `tests/unit/test_rc07_embedding_versioning.py` verifies:
- `MarqoFashionClipEmbedder` metadata (`model_id`, `model_version`, `dim`).
- `FakeEmbedder` protocol conformance and deterministic output.
- Refusal of `FakeEmbedder` under `ENV=production`.
- Environment-based default embedder resolution via `get_default_embedder()`.
