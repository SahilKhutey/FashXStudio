from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
from fashx.catalog.embeddings.ports import ImageTextEmbedder, validate_embedding_vector
from fashx.catalog.embeddings.service import get_default_embedder


def test_marqo_embedder_metadata_and_protocol() -> None:
    assert hasattr(MarqoFashionClipEmbedder, "embed_images")
    assert hasattr(MarqoFashionClipEmbedder, "embed_text")
    assert MarqoFashionClipEmbedder.model_id == "Marqo/marqo-fashionCLIP"
    assert MarqoFashionClipEmbedder.model_version == "2026.1"
    assert MarqoFashionClipEmbedder.dim == 512


def test_fake_embedder_metadata_and_protocol() -> None:
    embedder = FakeEmbedder()
    assert isinstance(embedder, ImageTextEmbedder)
    assert embedder.model_id == "mock-fake-512"
    assert embedder.model_version == "mock-v1"
    assert embedder.dim == 512


def test_vector_validation_catches_invalid_vectors() -> None:
    # Wrong dim
    with pytest.raises(ValueError, match="dimension mismatch"):
        validate_embedding_vector([0.1] * 128, expected_dim=512)

    # NaN / Inf
    bad_vec = [0.1] * 512
    bad_vec[10] = float("nan")
    with pytest.raises(ValueError, match="non-finite values"):
        validate_embedding_vector(bad_vec, expected_dim=512)

    bad_vec[10] = float("inf")
    with pytest.raises(ValueError, match="non-finite values"):
        validate_embedding_vector(bad_vec, expected_dim=512)

    # Zero norm
    zero_vec = [0.0] * 512
    with pytest.raises(ValueError, match="zero norm"):
        validate_embedding_vector(zero_vec, expected_dim=512)


def test_default_embedder_selection_by_environment() -> None:
    with patch.dict(os.environ, {"ENV": "dev"}):
        dev_embedder = get_default_embedder()
        assert isinstance(dev_embedder, FakeEmbedder)

    with patch.dict(os.environ, {"ENV": "test"}):
        test_embedder = get_default_embedder()
        assert isinstance(test_embedder, FakeEmbedder)
