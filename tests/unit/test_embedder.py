from __future__ import annotations

import math
import os
from unittest.mock import patch

import pytest

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.protocol import ImageEmbedder


def test_fake_embedder_protocol_conformance() -> None:
    embedder = FakeEmbedder()
    assert isinstance(embedder, ImageEmbedder)
    assert embedder.dim == 512
    assert embedder.model_id == "mock-fake-512"


def test_fake_embedder_deterministic_and_normalized() -> None:
    embedder = FakeEmbedder()
    img_a = b"sample_jpeg_image_bytes_123"
    img_b = b"different_image_bytes_456"

    vectors = embedder.embed_images([img_a, img_b, img_a])
    assert len(vectors) == 3
    assert len(vectors[0]) == 512
    assert len(vectors[1]) == 512

    # Determinism: identical input yields identical vector
    assert vectors[0] == vectors[2]
    # Distinct input yields distinct vector
    assert vectors[0] != vectors[1]

    # Unit normalization: norm should equal 1.0 (+- 1e-5)
    for v in vectors:
        norm = math.sqrt(sum(x * x for x in v))
        assert abs(norm - 1.0) < 1e-4


def test_fake_embedder_refuses_production() -> None:
    with patch.dict(os.environ, {"ENV": "production"}):
        with pytest.raises(RuntimeError, match="strictly forbidden in environment 'production'"):
            FakeEmbedder()


def test_fake_embedder_text_embedding() -> None:
    embedder = FakeEmbedder()
    texts = ["summer cotton floral kurta", "formal navy wool trousers"]
    vectors = embedder.embed_text(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 512
    assert vectors[0] != vectors[1]
