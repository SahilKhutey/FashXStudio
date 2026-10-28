"""Try-on eligibility evaluation logic and multi-factor catalog capability gates."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

TRYON_SUPPORTED_CATEGORIES: list[str] = [
    "tops",
    "bottoms",
    "one-pieces",
    "top",
    "bottom",
    "one_piece",
]


@dataclass(frozen=True)
class CatalogEligibility:
    """Multi-factor eligibility assessment determining customer surface capabilities."""

    discoverable: bool
    image_displayable: bool
    tryon_allowed: bool
    purchasable: bool
    reasons: tuple[str, ...]


def evaluate_eligibility(
    *,
    source_cleared: bool,
    display_rights: bool,
    image_validated: bool,
    tryon_rights: bool,
    stock_known: bool,
    in_stock: bool,
    product_url_valid: bool,
    category_valid: bool,
    price_valid: bool = True,
) -> CatalogEligibility:
    """Evaluate discrete item capabilities across discovery, image display, try-on, and checkout."""
    reasons: list[str] = []
    if not source_cleared:
        reasons.append("Source is not approved for ingestion")
    if not product_url_valid:
        reasons.append("Invalid or missing product destination URL")
    if not category_valid:
        reasons.append("Invalid product category")
    if not price_valid:
        reasons.append("Invalid or non-positive price")

    discoverable = bool(source_cleared and product_url_valid and category_valid and price_valid)
    image_displayable = bool(discoverable and display_rights and image_validated)
    tryon_allowed = bool(image_displayable and tryon_rights)
    purchasable = bool(discoverable and stock_known and in_stock)

    if discoverable and not image_displayable:
        reasons.append("Image display rights or byte validation missing")
    if image_displayable and not tryon_allowed:
        reasons.append("Virtual try-on rights not granted")
    if discoverable and not purchasable:
        reasons.append("Item is out of stock or inventory status unknown")

    return CatalogEligibility(
        discoverable=discoverable,
        image_displayable=image_displayable,
        tryon_allowed=tryon_allowed,
        purchasable=purchasable,
        reasons=tuple(reasons),
    )


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
