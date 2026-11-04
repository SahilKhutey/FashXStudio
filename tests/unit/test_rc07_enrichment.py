from __future__ import annotations

import io

import pytest
from PIL import Image

from fashx.catalog.enrichment.enricher import HeuristicGarmentEnricher


@pytest.mark.asyncio
async def test_enrichment_extracts_attributes_from_text() -> None:
    enricher = HeuristicGarmentEnricher()
    result = await enricher.enrich(
        title="Slim Fit Button-Down Formal Navy Shirt",
        description="100% cotton long sleeve shirt with solid pattern.",
    )

    assert result.attributes.silhouette == "slim"
    assert result.attributes.collar == "button_down"
    assert result.attributes.sleeve_length == "long"
    assert result.attributes.pattern == "solid"
    assert result.attributes.dominant_color == "navy"
    assert result.attributes.formality == "formal"
    assert result.attributes.material == "100% cotton"

    # Crucial architectural assertion: enricher never returns fabricated fake embeddings
    assert result.embedding is None
    assert result.model_version == "heuristic-enricher-v2"

    # Confidences are calibrated floats
    for k, v in result.confidence_summary.items():
        assert 0.0 <= v <= 1.0


@pytest.mark.asyncio
async def test_enrichment_fallback_and_color_from_image() -> None:
    enricher = HeuristicGarmentEnricher()

    # Generate a pure red test image
    img = Image.new("RGB", (200, 200), color=(240, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    result = await enricher.enrich(
        title="Casual Linen Kurta",
        description="Comfortable summer wear",
        image_bytes=image_bytes,
    )

    assert result.attributes.dominant_color == "red"
    assert result.attributes.material == "linen"
    assert result.attributes.formality == "casual"
    assert result.embedding is None


@pytest.mark.asyncio
async def test_enrichment_handles_empty_or_sparse_inputs() -> None:
    enricher = HeuristicGarmentEnricher()
    result = await enricher.enrich(title="", description=None, image_bytes=None)

    assert result.attributes.silhouette == "regular"
    assert result.attributes.pattern == "solid"
    assert result.embedding is None
    assert isinstance(result.confidence_summary, dict)
