from __future__ import annotations

import math
from collections.abc import Sequence

from fashx.catalog.embeddings.ports import validate_embedding_vector


def validate_vector_invariants(
    vector: Sequence[float],
    expected_dim: int = 512,
    tolerance: float = 1e-4,
    check_unit_norm: bool = True,
) -> None:
    """Validate vector dimensionality, numerical finiteness, non-zero norm, and unit length."""
    if len(vector) != expected_dim:
        raise ValueError(
            f"Embedding dimension mismatch: expected {expected_dim}, got {len(vector)}"
        )

    for i, val in enumerate(vector):
        if not math.isfinite(val):
            raise ValueError(
                f"Embedding vector contains non-finite value at index {i}: {val}"
            )

    norm_sq = sum(x * x for x in vector)
    norm = math.sqrt(norm_sq)

    if norm == 0.0 or math.isclose(norm, 0.0, abs_tol=1e-7):
        raise ValueError("Embedding vector has zero norm")

    if check_unit_norm and not math.isclose(norm, 1.0, abs_tol=tolerance):
        raise ValueError(
            f"Embedding vector is not L2-normalized: expected norm ~1.0, got {norm:.6f}"
        )


__all__ = [
    "validate_embedding_vector",
    "validate_vector_invariants",
]
