from __future__ import annotations

import math

import pytest

from fashx.catalog.embeddings.base import ImageEmbeddingAdapter
from fashx.catalog.embeddings.models.mock_adapter import MockViTB32Adapter
from fashx.catalog.embeddings.registry import EmbeddingModelRegistry
from fashx.catalog.embeddings.validation import validate_vector_invariants


def test_emb_001_model_registry_approved() -> None:
    """Verify EMB-001: Approved model registry contains OpenCLIP ViT-B/32."""
    registry = EmbeddingModelRegistry.get_instance()
    meta = registry.get_metadata("openclip_vit_b32", "v1")
    assert meta.model_id == "openclip_vit_b32"
    assert meta.model_version == "v1"
    assert meta.dimension == 512
    assert "ViT-B/32" in meta.architecture


def test_emb_002_adapter_protocol() -> None:
    """Verify EMB-002: Adapter implements ImageEmbeddingAdapter protocol."""
    adapter = MockViTB32Adapter()
    assert isinstance(adapter, ImageEmbeddingAdapter)
    assert adapter.model_id == "openclip_vit_b32"
    assert adapter.dimension == 512
    assert hasattr(adapter, "embed_image")
    assert hasattr(adapter, "embed_batch")


def test_emb_003_vector_dimension_512(sample_image_bytes: bytes) -> None:
    """Verify EMB-003: Generated vectors have exactly 512 dimensions."""
    adapter = MockViTB32Adapter()
    vec = adapter.embed_image(sample_image_bytes)
    assert isinstance(vec, list)
    assert len(vec) == 512
    assert all(isinstance(x, float) for x in vec)


def test_emb_004_vector_l2_normalization(sample_image_bytes: bytes) -> None:
    """Verify EMB-004: Generated vectors are strictly L2-normalized (norm ~ 1.0)."""
    adapter = MockViTB32Adapter()
    vec = adapter.embed_image(sample_image_bytes)
    norm = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(norm, 1.0, abs_tol=1e-4)


def test_emb_005_reject_nan_inf() -> None:
    """Verify EMB-005: Vector validation rejects NaN or Infinite values."""
    valid_vec = [1.0 / math.sqrt(512)] * 512
    validate_vector_invariants(valid_vec)

    # Poison with NaN
    nan_vec = list(valid_vec)
    nan_vec[10] = float("nan")
    with pytest.raises(ValueError, match="non-finite value at index 10"):
        validate_vector_invariants(nan_vec)

    # Poison with Inf
    inf_vec = list(valid_vec)
    inf_vec[25] = float("inf")
    with pytest.raises(ValueError, match="non-finite value at index 25"):
        validate_vector_invariants(inf_vec)


def test_emb_006_reject_zero_norm() -> None:
    """Verify EMB-006: Vector validation rejects zero norm."""
    zero_vec = [0.0] * 512
    with pytest.raises(ValueError, match="zero norm"):
        validate_vector_invariants(zero_vec)


def test_emb_007_deterministic_inference(sample_image_bytes: bytes) -> None:
    """Verify EMB-007: Repeated embeddings of identical image yield identical vectors."""
    adapter = MockViTB32Adapter()
    vec1 = adapter.embed_image(sample_image_bytes)
    vec2 = adapter.embed_image(sample_image_bytes)

    assert len(vec1) == len(vec2) == 512
    for x1, x2 in zip(vec1, vec2, strict=True):
        assert math.isclose(x1, x2, abs_tol=1e-7)
