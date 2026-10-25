"""Enrichment job contract, embedding validation, and state machine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class EnrichmentJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"


@dataclass(frozen=True)
class GarmentEnrichmentJob:
    """Enrichment task payload linking validated image provenance to inference."""

    garment_id: UUID
    image_id: UUID
    image_content_hash: str
    model_version: str = "marqo-fashionclip-v1"
    requested_tasks: tuple[str, ...] = (
        "category",
        "dominant_color",
        "silhouette",
        "visual_embedding",
    )


def validate_embedding(
    embedding: list[float],
    *,
    expected_dimension: int = 512,
) -> None:
    """Validate visual embedding vector, strictly excluding zero or constant placeholder vectors."""
    if not isinstance(embedding, list):
        raise ValueError("Embedding must be a list of floats")

    if len(embedding) != expected_dimension:
        raise ValueError(
            f"Unexpected embedding dimension: got {len(embedding)}, expected {expected_dimension}"
        )

    if not all(math.isfinite(val) for val in embedding):
        raise ValueError("Embedding vector contains non-finite values (NaN or Inf)")

    if not any(abs(val) > 1e-12 for val in embedding):
        raise ValueError("Embedding vector is completely zero-valued")

    # Guard against constant placeholder vectors (e.g. [0.05] * 512)
    first_val = embedding[0]
    if all(abs(val - first_val) < 1e-9 for val in embedding):
        raise ValueError(
            f"Embedding is an uninformative constant placeholder vector of value {first_val}"
        )
