from __future__ import annotations

import io
import math

import pytest
from PIL import Image

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.service import EmbeddingResult, EmbeddingService


def make_valid_image(width: int = 150, height: int = 150) -> bytes:
    img = Image.new("RGB", (width, height), color=(120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_embedding_service_image_embedding() -> None:
    embedder = FakeEmbedder()
    service = EmbeddingService(embedder)

    img_bytes = make_valid_image()
    res = service.embed_image(img_bytes)

    assert isinstance(res, EmbeddingResult)
    assert res.dim == 512
    assert len(res.vector) == 512
    assert res.model_id == "mock-fake-512"
    assert res.model_version == "mock-v1"
    assert res.model_key == "mock-fake-512:mock-v1"

    norm = math.sqrt(sum(x * x for x in res.vector))
    assert abs(norm - 1.0) < 1e-4


def test_embedding_service_rejects_empty_and_corrupt_image() -> None:
    embedder = FakeEmbedder()
    service = EmbeddingService(embedder)

    with pytest.raises(ValueError, match="Image is empty"):
        service.embed_image(b"")

    with pytest.raises(ValueError, match="Malformed or unrecognized"):
        service.embed_image(b"invalid_non_image_payload")


def test_embedding_service_text_embedding() -> None:
    embedder = FakeEmbedder()
    service = EmbeddingService(embedder)

    res = service.embed_text("summer linen casual kurta")
    assert isinstance(res, EmbeddingResult)
    assert res.dim == 512
    assert len(res.vector) == 512

    with pytest.raises(ValueError, match="empty or whitespace-only"):
        service.embed_text("   ")


def test_embedding_service_batches() -> None:
    embedder = FakeEmbedder()
    service = EmbeddingService(embedder)

    img1 = make_valid_image(150, 150)
    img2 = make_valid_image(200, 200)

    results = service.embed_images_batch([img1, img2])
    assert len(results) == 2
    assert results[0].dim == 512
    assert results[1].dim == 512

    text_results = service.embed_texts_batch(["red silk saree", "blue denim jacket"])
    assert len(text_results) == 2
    assert text_results[0].vector != text_results[1].vector
