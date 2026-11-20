from __future__ import annotations

import re
from dataclasses import dataclass

from fashx.catalog.taxonomy.registry import TaxonomyRegistry

KNOWN_CATEGORY_MAPPINGS: dict[str, str] = {
    # Tops / T-shirts
    "men > clothing > t-shirts": "apparel_tops_t_shirts",
    "men's clothing / t-shirts": "apparel_tops_t_shirts",
    "men / clothing / t-shirts": "apparel_tops_t_shirts",
    "men / tops / t-shirts": "apparel_tops_t_shirts",
    "women > clothing > t-shirts": "apparel_tops_t_shirts",
    "women's clothing / t-shirts": "apparel_tops_t_shirts",
    "t-shirts": "apparel_tops_t_shirts",
    # Shirts
    "men > clothing > shirts": "apparel_tops_shirts",
    "men / casual shirts": "apparel_tops_shirts",
    "men / formal shirts": "apparel_tops_shirts",
    "casual shirts": "apparel_tops_shirts",
    "shirts": "apparel_tops_shirts",
    # Ethnic Wear / Kurtas & Kurtis
    "ethnic wear / men's kurtas": "ethnic_wear_kurtas_and_kurtis",
    "men's ethnic short kurta": "ethnic_wear_kurtas_and_kurtis",
    "women / kurtis": "ethnic_wear_kurtas_and_kurtis",
    "kurtas & kurtis": "ethnic_wear_kurtas_and_kurtis",
    "kurtas": "ethnic_wear_kurtas_and_kurtis",
    "kurtis": "ethnic_wear_kurtas_and_kurtis",
    # Bottoms / Jeans
    "men > clothing > jeans": "apparel_bottoms_jeans",
    "women > clothing > jeans": "apparel_bottoms_jeans",
    "jeans": "apparel_bottoms_jeans",
    # Footwear / Sneakers
    "footwear / sneakers": "footwear_sneakers",
    "men / footwear / sneakers": "footwear_sneakers",
    "sneakers": "footwear_sneakers",
    # Accessories
    "accessories / handbags": "accessories_bags_handbags",
    "handbags": "accessories_bags_handbags",
}


@dataclass(frozen=True)
class CategoryMappingResult:
    category_id: str | None
    is_leaf: bool
    confidence: float
    mapped_from: str
    quarantined: bool = False
    ambiguity_reason: str | None = None


def normalize_category_string(cat_str: str) -> str:
    """Normalize raw merchant category string for lookup."""
    lowered = cat_str.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def map_merchant_category(
    merchant_category: str | None,
    registry: TaxonomyRegistry,
) -> CategoryMappingResult:
    """Map raw merchant category into an approved Phase 6.1 taxonomy category node."""
    if not merchant_category or not merchant_category.strip():
        return CategoryMappingResult(
            category_id=None,
            is_leaf=False,
            confidence=0.0,
            mapped_from="",
            quarantined=True,
            ambiguity_reason="EMPTY_MERCHANT_CATEGORY",
        )

    raw_norm = normalize_category_string(merchant_category)

    # 1. Exact alias / known mappings check
    if raw_norm in KNOWN_CATEGORY_MAPPINGS:
        cat_id = KNOWN_CATEGORY_MAPPINGS[raw_norm]
        node = registry.get_category(cat_id)
        if node is not None:
            return CategoryMappingResult(
                category_id=cat_id,
                is_leaf=node.is_leaf,
                confidence=0.99,
                mapped_from=merchant_category,
            )

    # 2. Check if raw string is already an exact category_id in registry
    node = registry.get_category(raw_norm)
    if node is not None:
        return CategoryMappingResult(
            category_id=node.category_id,
            is_leaf=node.is_leaf,
            confidence=1.0,
            mapped_from=merchant_category,
        )

    # 3. Check alias resolution from taxonomy registry
    resolved_code = registry.resolve_alias("category", raw_norm)
    if resolved_code is not None:
        node = registry.get_category(resolved_code)
        if node is not None:
            return CategoryMappingResult(
                category_id=node.category_id,
                is_leaf=node.is_leaf,
                confidence=0.98,
                mapped_from=merchant_category,
            )

    # 4. Check path tokens against taxonomy leaf categories
    tokens = [t.strip() for t in re.split(r"[/>,]", raw_norm) if t.strip()]
    for token in reversed(tokens):
        if token in KNOWN_CATEGORY_MAPPINGS:
            cat_id = KNOWN_CATEGORY_MAPPINGS[token]
            node = registry.get_category(cat_id)
            if node is not None:
                return CategoryMappingResult(
                    category_id=cat_id,
                    is_leaf=node.is_leaf,
                    confidence=0.92,
                    mapped_from=merchant_category,
                )

    # 5. Fallback: Never default unknown category to tops/shirts (Rule 6.2.4 & ENR-010)
    return CategoryMappingResult(
        category_id=None,
        is_leaf=False,
        confidence=0.0,
        mapped_from=merchant_category,
        quarantined=True,
        ambiguity_reason="UNRESOLVED_CATEGORY_QUARANTINED",
    )
