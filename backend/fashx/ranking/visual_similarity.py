"""Compatible, permission-checked visual similarity scoring (Task 8.4.8)."""

from __future__ import annotations

import math
from collections.abc import Sequence


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        raise ValueError("Embedding vectors must be non-empty and have equal dimensions")
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def normalize_cosine_similarity(
    similarity: float,
    lower_bound: float,
    upper_bound: float,
) -> float:
    """Calibrate raw cosine similarity into [0.0, 1.0]."""
    if upper_bound <= lower_bound:
        raise ValueError("Invalid similarity calibration bounds")
    return max(0.0, min(1.0, (similarity - lower_bound) / (upper_bound - lower_bound)))


def compute_visual_similarity(
    reference_embedding: Sequence[float] | None,
    candidate_embedding: Sequence[float] | None,
    *,
    reference_model: str | None,
    candidate_model: str | None,
    reference_version: str | None,
    candidate_version: str | None,
    reference_preprocessing_version: str | None = None,
    candidate_preprocessing_version: str | None = None,
    permission_granted: bool = True,
    lower_bound: float = 0.0,
    upper_bound: float = 1.0,
) -> float | None:
    """Compute calibrated visual similarity only when embeddings are compatible and authorized."""
    if reference_embedding is None or candidate_embedding is None:
        return None
    if not permission_granted:
        raise PermissionError("Reference image permission is not granted")
    if (
        not reference_model
        or reference_model != candidate_model
        or reference_version != candidate_version
        or reference_preprocessing_version != candidate_preprocessing_version
    ):
        raise ValueError("Incompatible embedding model or preprocessing versions")
    if len(reference_embedding) != len(candidate_embedding):
        raise ValueError("Incompatible embedding dimensions")

    raw_sim = cosine_similarity(reference_embedding, candidate_embedding)
    return normalize_cosine_similarity(raw_sim, lower_bound, upper_bound)
