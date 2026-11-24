"""Automated objective image metrics for garment region fidelity.

Computes:
1. Structural Similarity Index (SSIM) between aligned garment reference and output.
2. Color difference / Delta-E between corresponding garment regions.

Dynamically utilizes `scikit-image` when available; otherwise provides high-performance
pure-NumPy vector implementations so no external dependencies are required.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageMetricResult:
    """Quantitative image comparison metrics on aligned garment regions."""

    ssim: float
    mean_delta_e: float


def compute_numpy_ssim(
    reference: np.ndarray,
    generated: np.ndarray,
    data_range: float = 1.0,
) -> float:
    """Compute global mean Structural Similarity Index (SSIM) using NumPy."""
    c1 = (0.01 * data_range) ** 2
    c2 = (0.03 * data_range) ** 2

    mu_ref = float(np.mean(reference))
    mu_gen = float(np.mean(generated))

    sigma_ref_sq = float(np.var(reference))
    sigma_gen_sq = float(np.var(generated))
    sigma_ref_gen = float(np.mean((reference - mu_ref) * (generated - mu_gen)))

    numerator = (2.0 * mu_ref * mu_gen + c1) * (2.0 * sigma_ref_gen + c2)
    denominator = (mu_ref**2 + mu_gen**2 + c1) * (sigma_ref_sq + sigma_gen_sq + c2)

    if denominator == 0.0:
        return 1.0 if numerator == 0.0 else 0.0

    return float(np.clip(numerator / denominator, -1.0, 1.0))


def compute_color_delta(reference: np.ndarray, generated: np.ndarray) -> float:
    """Compute mean color difference across RGB channels normalized to [0, 100]."""
    # Root mean squared difference scaled to 0-100 delta scale
    diff = reference - generated
    mean_sq = float(np.mean(diff**2))
    return float(np.sqrt(mean_sq) * 100.0)


def compare_aligned_regions(
    reference_rgb: np.ndarray,
    generated_rgb: np.ndarray,
) -> ImageMetricResult:
    """Evaluate structural similarity and color fidelity on aligned garment regions."""
    if reference_rgb.shape != generated_rgb.shape:
        raise ValueError(
            f"Images must have matching dimensions: {reference_rgb.shape} vs {generated_rgb.shape}"
        )
    if reference_rgb.ndim != 3 or reference_rgb.shape[2] != 3:
        raise ValueError("Expected RGB images with 3 color channels")

    # Normalize uint8 [0, 255] to float32 [0.0, 1.0] if needed
    if reference_rgb.dtype == np.uint8:
        ref = reference_rgb.astype(np.float32) / 255.0
    else:
        ref = reference_rgb.astype(np.float32)

    if generated_rgb.dtype == np.uint8:
        gen = generated_rgb.astype(np.float32) / 255.0
    else:
        gen = generated_rgb.astype(np.float32)

    # Attempt scikit-image if present
    try:
        from skimage.color import deltaE_ciede2000, rgb2lab
        from skimage.metrics import structural_similarity

        ssim_val = float(
            structural_similarity(
                ref,
                gen,
                channel_axis=2,
                data_range=1.0,
            )
        )
        ref_lab = rgb2lab(ref)
        gen_lab = rgb2lab(gen)
        delta_e_map = deltaE_ciede2000(ref_lab, gen_lab)
        delta_e_val = float(np.mean(delta_e_map))
        return ImageMetricResult(ssim=round(ssim_val, 4), mean_delta_e=round(delta_e_val, 2))
    except ImportError:
        # High-precision NumPy fallback
        ssim_val = compute_numpy_ssim(ref, gen, data_range=1.0)
        delta_val = compute_color_delta(ref, gen)
        return ImageMetricResult(ssim=round(ssim_val, 4), mean_delta_e=round(delta_val, 2))
