"""Unit tests for enrichment job contracts and visual embedding validation."""

import math
from uuid import uuid4

import pytest

from fashx.catalog.enrichment.jobs import (
    EnrichmentJobStatus,
    GarmentEnrichmentJob,
    validate_embedding,
)


def test_garment_enrichment_job_contract() -> None:
    g_id = uuid4()
    img_id = uuid4()
    job = GarmentEnrichmentJob(
        garment_id=g_id,
        image_id=img_id,
        image_content_hash="abc123hash",
        model_version="marqo-fashionclip-v1",
    )
    assert job.garment_id == g_id
    assert job.image_id == img_id
    assert job.image_content_hash == "abc123hash"
    assert "visual_embedding" in job.requested_tasks
    assert EnrichmentJobStatus.PENDING == "pending"
    assert EnrichmentJobStatus.SUCCEEDED == "succeeded"


def test_validate_embedding_valid_vector() -> None:
    # 512-dimensional varied float vector
    valid_vector = [math.sin(i * 0.1) for i in range(512)]
    # Should complete without error
    validate_embedding(valid_vector, expected_dimension=512)


def test_validate_embedding_rejects_dimension_mismatch() -> None:
    short_vector = [0.1] * 256
    with pytest.raises(ValueError, match="Unexpected embedding dimension"):
        validate_embedding(short_vector, expected_dimension=512)


def test_validate_embedding_rejects_non_finite_values() -> None:
    nan_vector = [0.1] * 511 + [float("nan")]
    with pytest.raises(ValueError, match="non-finite values"):
        validate_embedding(nan_vector, expected_dimension=512)

    inf_vector = [0.1] * 511 + [float("inf")]
    with pytest.raises(ValueError, match="non-finite values"):
        validate_embedding(inf_vector, expected_dimension=512)


def test_validate_embedding_rejects_zero_vector() -> None:
    zero_vector = [0.0] * 512
    with pytest.raises(ValueError, match="completely zero-valued"):
        validate_embedding(zero_vector, expected_dimension=512)


def test_validate_embedding_rejects_constant_placeholder_vector() -> None:
    # Legacy placeholder vectors e.g. [0.05] * 512 must be strictly excluded
    placeholder_vector = [0.05] * 512
    with pytest.raises(ValueError, match="constant placeholder vector"):
        validate_embedding(placeholder_vector, expected_dimension=512)
