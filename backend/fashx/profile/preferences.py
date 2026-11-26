"""Subjective fit preferences & brand-size independence guards (Phase 08.2 - Tasks 8.2.8, 8.2.9, 8.2.10)."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_CATEGORIES = frozenset(
    {
        "TSHIRTS",
        "SHIRTS",
        "KURTAS",
        "TOPS",
        "TROUSERS",
        "JEANS",
        "DRESSES",
        "SKIRTS",
    }
)

SUPPORTED_FIT_PREFERENCES = frozenset(
    {
        "SLIM",
        "REGULAR",
        "RELAXED",
        "OVERSIZED",
        "NO_PREFERENCE",
    }
)


class BrandSizeMappingError(ValueError):
    """Raised when unsupported cross-brand size equivalence is attempted."""


@dataclass(frozen=True)
class CategoryPreference:
    """Subjective shopper fit preference for a single garment category."""

    category: str
    fit_preference: str


def validate_category(category: str) -> str:
    """Validate and normalize a category identifier against supported taxonomy."""
    norm = category.strip().upper()
    if norm not in SUPPORTED_CATEGORIES:
        raise ValueError(
            f"Unsupported category '{category}'. Supported categories: {', '.join(sorted(SUPPORTED_CATEGORIES))}."
        )
    return norm


def validate_fit_preference(fit_preference: str) -> str:
    """Validate and normalize subjective fit preference enum values."""
    norm = fit_preference.strip().upper()
    if norm not in SUPPORTED_FIT_PREFERENCES:
        raise ValueError(
            f"Invalid fit preference '{fit_preference}'. Supported options: {', '.join(sorted(SUPPORTED_FIT_PREFERENCES))}."
        )
    return norm


def resolve_fit_preference(
    category: str,
    category_preferences: dict[str, str],
    default_preference: str | None,
) -> str:
    """Resolve shopper fit preference deterministically without cross-category inference.

    Precedence:
    1. Explicit category preference (only if category is supported).
    2. Explicit default fit preference (unless NO_PREFERENCE / None).
    3. NO_PREFERENCE.
    """
    norm_cat = category.strip().upper()
    if norm_cat not in SUPPORTED_CATEGORIES:
        return "NO_PREFERENCE"

    norm_map = {k.strip().upper(): v.strip().upper() for k, v in category_preferences.items()}
    if norm_cat in norm_map and norm_map[norm_cat] in SUPPORTED_FIT_PREFERENCES:
        return norm_map[norm_cat]

    if default_preference is not None:
        norm_def = default_preference.strip().upper()
        if norm_def in SUPPORTED_FIT_PREFERENCES:
            return norm_def

    return "NO_PREFERENCE"


def ensure_no_brand_size_assumption(
    *,
    has_product_chart: bool,
    has_chart_basis: bool,
    has_required_body_measurements: bool,
) -> None:
    """Enforce Task 8.2.10: prohibit cross-brand size mapping or unbacked fit evidence."""
    if not has_product_chart or not has_chart_basis or not has_required_body_measurements:
        raise BrandSizeMappingError(
            "INSUFFICIENT_DATA: A shopper's fit profile or declared brand size cannot be converted into another "
            "brand's size label without an active, basis-verified merchant product chart and required body measurements."
        )
