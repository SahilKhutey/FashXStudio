"""Category policy defining required body regions and support status (Phase 07.3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CategorySupportStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PENDING = "PENDING"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CategoryPolicy:
    category: str
    status: CategorySupportStatus
    required_regions: set[str]
    description: str


# Canonical category definitions
CATEGORY_POLICIES: dict[str, CategoryPolicy] = {
    # Tops
    "tops": CategoryPolicy(
        category="tops",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso"},
        description="Upper body garments including t-shirts, shirts, tops, blouses, and kurtas",
    ),
    "tshirt": CategoryPolicy(
        category="tshirt",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso"},
        description="T-Shirts",
    ),
    "shirt": CategoryPolicy(
        category="shirt",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso"},
        description="Formal and casual shirts",
    ),
    "kurta": CategoryPolicy(
        category="kurta",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso"},
        description="Ethnic and casual kurtas",
    ),
    # Bottoms
    "bottoms": CategoryPolicy(
        category="bottoms",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"waist", "legs"},
        description="Lower body garments including trousers, pants, jeans, and skirts",
    ),
    "trousers": CategoryPolicy(
        category="trousers",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"waist", "legs"},
        description="Formal and casual trousers",
    ),
    # One-pieces
    "one-pieces": CategoryPolicy(
        category="one-pieces",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso", "legs"},
        description="Full body one-piece apparel including dresses, jumpsuits, and rompers",
    ),
    "dress": CategoryPolicy(
        category="dress",
        status=CategorySupportStatus.SUPPORTED,
        required_regions={"shoulders", "torso", "legs"},
        description="Full dresses",
    ),
    # Pending evaluation
    "saree": CategoryPolicy(
        category="saree",
        status=CategorySupportStatus.PENDING,
        required_regions={"shoulders", "torso", "waist", "legs"},
        description="Sarees (pending specialized drape workflow evaluation)",
    ),
    "lehenga": CategoryPolicy(
        category="lehenga",
        status=CategorySupportStatus.PENDING,
        required_regions={"torso", "waist", "legs"},
        description="Lehengas (pending specialized drape workflow evaluation)",
    ),
    # Unsupported categories
    "footwear": CategoryPolicy(
        category="footwear",
        status=CategorySupportStatus.UNSUPPORTED,
        required_regions=set(),
        description="Shoes and footwear (unsupported in apparel VTO)",
    ),
    "jewellery": CategoryPolicy(
        category="jewellery",
        status=CategorySupportStatus.UNSUPPORTED,
        required_regions=set(),
        description="Jewellery and accessories (unsupported in apparel VTO)",
    ),
}


def get_category_policy(category: str) -> CategoryPolicy:
    """Resolve normalized CategoryPolicy or return conservative unsupported fallback."""
    cat_lower = (category or "").strip().lower()

    # Map common aliases
    alias_map = {
        "top": "tops",
        "t-shirt": "tshirt",
        "t-shirts": "tshirt",
        "shirts": "shirt",
        "kurtas": "kurta",
        "bottom": "bottoms",
        "pants": "bottoms",
        "jeans": "bottoms",
        "one_piece": "one-pieces",
        "onepiece": "one-pieces",
        "dresses": "dress",
        "sarees": "saree",
        "lehengas": "lehenga",
        "shoes": "footwear",
        "jewelry": "jewellery",
        "accessory": "jewellery",
        "accessories": "jewellery",
    }
    canonical = alias_map.get(cat_lower, cat_lower)

    if canonical in CATEGORY_POLICIES:
        return CATEGORY_POLICIES[canonical]

    # Default fallback: unsupported category
    return CategoryPolicy(
        category=category,
        status=CategorySupportStatus.UNSUPPORTED,
        required_regions=set(),
        description=f"Unrecognized or unsupported category: '{category}'",
    )
