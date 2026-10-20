"""Try-on eligibility evaluation logic (Phase 6 / Step 6.25 multi-factor gate)."""

from __future__ import annotations

from collections.abc import Sequence

TRYON_SUPPORTED_CATEGORIES: list[str] = [
    "tops",
    "bottoms",
    "one-pieces",
    "top",
    "bottom",
    "one_piece",
]


def compute_tryon_eligibility(
    *,
    source_rights_tryon: bool,
    source_image_policy: str,
    vlm_tryon_suitable: bool = True,
    vlm_confidence: float = 1.0,
    category: str = "tops",
    supported_categories: Sequence[str] = TRYON_SUPPORTED_CATEGORIES,
    tau: float = 0.85,
) -> bool:
    """Evaluate 4-point try-on eligibility gate.
    Requires:
      1. source_rights_tryon is True
      2. source_image_policy == 'mirror'
      3. vlm_tryon_suitable is True
      4. vlm_confidence >= tau (0.85)
      5. category in supported_categories
    """
    if not source_rights_tryon:
        return False
    if source_image_policy != "mirror":
        return False
    if not vlm_tryon_suitable:
        return False
    if vlm_confidence < tau:
        return False
    if category.lower() not in [c.lower() for c in supported_categories]:
        return False
    return True
