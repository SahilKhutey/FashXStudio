"""Unit tests for automated objective image metrics (Phase 07.7)."""

from __future__ import annotations

import numpy as np
import pytest

from fashx.tryon.evaluation.image_metrics import (
    compare_aligned_regions,
)


def test_identical_images_produce_perfect_scores():
    """METRIC-001: Identical images produce SSIM = 1.0 and Delta-E = 0.0."""
    img1 = np.full((64, 64, 3), 128, dtype=np.uint8)
    img2 = np.full((64, 64, 3), 128, dtype=np.uint8)

    res = compare_aligned_regions(img1, img2)
    assert res.ssim == 1.0
    assert res.mean_delta_e == 0.0


def test_perturbed_images_reduce_scores():
    """METRIC-002: Perturbed images produce SSIM < 1.0 and Delta-E > 0.0."""
    img1 = np.full((64, 64, 3), 128, dtype=np.uint8)
    img2 = np.full((64, 64, 3), 160, dtype=np.uint8)

    res = compare_aligned_regions(img1, img2)
    assert res.ssim < 1.0
    assert res.mean_delta_e > 0.0


def test_mismatched_dimensions_raise_error():
    """METRIC-003: Mismatched image dimensions raise ValueError."""
    img1 = np.zeros((64, 64, 3), dtype=np.uint8)
    img2 = np.zeros((32, 32, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="Images must have matching dimensions"):
        compare_aligned_regions(img1, img2)
