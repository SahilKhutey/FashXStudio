from decimal import Decimal

from .entities import RecommendationCandidate


def calculate_score(
    *,
    personalization: Decimal,
    context: Decimal,
    price: Decimal,
    region: Decimal,
    source: Decimal,
) -> Decimal:
    score = (
        Decimal("0.55") * personalization
        + Decimal("0.20") * context
        + Decimal("0.10") * price
        + Decimal("0.05") * region
        + Decimal("0.10") * source
    )

    return max(
        Decimal("0"),
        min(Decimal("1"), score),
    )


def rank_candidates(
    candidates: list[
        tuple[
            RecommendationCandidate,
            Decimal,
        ]
    ],
) -> list[
    tuple[
        RecommendationCandidate,
        Decimal,
    ]
]:
    return sorted(
        candidates,
        key=lambda item: (
            item[1],
            str(item[0].product_id),
        ),
        reverse=True,
    )


def apply_diversity(
    ranked_candidates: list[
        tuple[
            RecommendationCandidate,
            Decimal,
        ]
    ],
    *,
    max_per_brand: int = 4,
    max_per_category: int = 6,
) -> list[
    tuple[
        RecommendationCandidate,
        Decimal,
    ]
]:
    brand_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    selected: list[tuple[RecommendationCandidate, Decimal]] = []
    overflow: list[tuple[RecommendationCandidate, Decimal]] = []

    for candidate, score in ranked_candidates:
        brand_key = candidate.brand.lower() if candidate.brand else None
        cat_key = candidate.category.lower() if candidate.category else None

        brand_ok = brand_key is None or brand_counts.get(brand_key, 0) < max_per_brand
        cat_ok = cat_key is None or category_counts.get(cat_key, 0) < max_per_category

        if brand_ok and cat_ok:
            if brand_key:
                brand_counts[brand_key] = brand_counts.get(brand_key, 0) + 1
            if cat_key:
                category_counts[cat_key] = category_counts.get(cat_key, 0) + 1
            selected.append((candidate, score))
        else:
            overflow.append((candidate, score))

    return selected + overflow
