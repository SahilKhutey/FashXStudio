"""Versioned category fit policies (Phase 08.3 - Task 8.3.2).

Keeps release-gated category policies separate from general browse profiles so
unvalidated categories (e.g. trousers in the initial launch slice, sarees, lehengas)
fail closed without guessing requirements or inventing fit rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from fashx.fit.enums import FitPreference, MeasurementBasis
from fashx.profile.fit_policy import FIT_POLICY_VERSION


class UnsupportedCategoryFitError(ValueError):
    """Raised when fit policy is requested strictly for an unsupported/disabled category."""


@dataclass(frozen=True)
class CategoryFitPolicy:
    """Category-specific requirements, compatible bases, and release gate state."""

    category: str
    taxonomy_version: str
    version: str
    required_measurements: tuple[str, ...]
    required_chart_measurements: tuple[str, ...]
    optional_measurements: tuple[str, ...]
    supported_bases: tuple[MeasurementBasis, ...]
    supported_fit_preferences: tuple[FitPreference, ...]
    ease_policy_id: str | None
    enabled: bool
    rationale: str


CATEGORY_POLICIES: dict[str, CategoryFitPolicy] = {
    "TSHIRTS": CategoryFitPolicy(
        category="TSHIRTS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("CHEST",),
        required_chart_measurements=("CHEST",),
        optional_measurements=("SHOULDER", "BODY_LENGTH", "SLEEVE_LENGTH"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(
            FitPreference.SLIM,
            FitPreference.REGULAR,
            FitPreference.RELAXED,
            FitPreference.OVERSIZED,
            FitPreference.NO_PREFERENCE,
        ),
        ease_policy_id=None,
        enabled=True,
        rationale="Initial controlled launch category anchored on published chest body-range matching.",
    ),
    "SHIRTS": CategoryFitPolicy(
        category="SHIRTS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("CHEST",),
        required_chart_measurements=("CHEST",),
        optional_measurements=("SHOULDER", "NECK", "SLEEVE_LENGTH", "WAIST"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.REGULAR, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Awaiting validated merchant shirt collar/sleeve chart coverage before release.",
    ),
    "KURTAS": CategoryFitPolicy(
        category="KURTAS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("CHEST",),
        required_chart_measurements=("CHEST",),
        optional_measurements=("SHOULDER", "LENGTH", "WAIST"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.REGULAR, FitPreference.RELAXED, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Disabled pending validated ethnic-wear ease and silhouette evidence.",
    ),
    "TOPS": CategoryFitPolicy(
        category="TOPS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("BUST",),
        required_chart_measurements=("BUST",),
        optional_measurements=("SHOULDER", "WAIST", "LENGTH"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.REGULAR, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Disabled pending bust/chest merchant chart standardization review.",
    ),
    "TROUSERS": CategoryFitPolicy(
        category="TROUSERS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("WAIST", "HIP"),
        required_chart_measurements=("WAIST", "HIP"),
        optional_measurements=("INSEAM", "RISE"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.SLIM, FitPreference.REGULAR, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Intentionally disabled until waist/hip/inseam fit rules pass manual labelling evaluation.",
    ),
    "JEANS": CategoryFitPolicy(
        category="JEANS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("WAIST", "HIP"),
        required_chart_measurements=("WAIST", "HIP"),
        optional_measurements=("INSEAM", "RISE", "THIGH"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.SLIM, FitPreference.REGULAR, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Disabled pending denim stretch/ease validation.",
    ),
    "DRESSES": CategoryFitPolicy(
        category="DRESSES",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("BUST", "WAIST", "HIP"),
        required_chart_measurements=("BUST", "WAIST", "HIP"),
        optional_measurements=("LENGTH", "SHOULDER"),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.REGULAR, FitPreference.NO_PREFERENCE),
        ease_policy_id=None,
        enabled=False,
        rationale="Disabled pending multi-point bust/waist/hip silhouette validation.",
    ),
    "SAREES": CategoryFitPolicy(
        category="SAREES",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=(),
        required_chart_measurements=(),
        optional_measurements=(),
        supported_bases=(),
        supported_fit_preferences=(FitPreference.NO_PREFERENCE,),
        ease_policy_id=None,
        enabled=False,
        rationale="Sarees are draped garments not covered by single-size dimensional fit matching.",
    ),
    "LEHENGAS": CategoryFitPolicy(
        category="LEHENGAS",
        taxonomy_version="1.0",
        version=FIT_POLICY_VERSION,
        required_measurements=("WAIST", "HIP"),
        required_chart_measurements=("WAIST", "HIP"),
        optional_measurements=("LENGTH",),
        supported_bases=(MeasurementBasis.BODY,),
        supported_fit_preferences=(FitPreference.NO_PREFERENCE,),
        ease_policy_id=None,
        enabled=False,
        rationale="Disabled pending waist/hip and drape validation.",
    ),
}

_CATEGORY_ALIASES: dict[str, str] = {
    "T_SHIRT": "TSHIRTS",
    "T_SHIRTS": "TSHIRTS",
    "TSHIRT": "TSHIRTS",
    "TSHIRTS": "TSHIRTS",
    "TEE": "TSHIRTS",
    "TEES": "TSHIRTS",
    "SHIRT": "SHIRTS",
    "SHIRTS": "SHIRTS",
    "CASUAL_SHIRT": "SHIRTS",
    "CASUAL_SHIRTS": "SHIRTS",
    "FORMAL_SHIRT": "SHIRTS",
    "FORMAL_SHIRTS": "SHIRTS",
    "KURTA": "KURTAS",
    "KURTAS": "KURTAS",
    "TOP": "TOPS",
    "TOPS": "TOPS",
    "TROUSER": "TROUSERS",
    "TROUSERS": "TROUSERS",
    "PANTS": "TROUSERS",
    "JEAN": "JEANS",
    "JEANS": "JEANS",
    "DRESS": "DRESSES",
    "DRESSES": "DRESSES",
    "SAREE": "SAREES",
    "SAREES": "SAREES",
    "LEHENGA": "LEHENGAS",
    "LEHENGAS": "LEHENGAS",
}


def normalize_category_code(raw_category: str | None) -> str:
    """Normalize raw category text to canonical taxonomy code without inventing support."""
    if not raw_category or not raw_category.strip():
        return "UNKNOWN"
    cleaned = raw_category.strip().upper().replace("-", "_").replace(" ", "_")
    return _CATEGORY_ALIASES.get(cleaned, cleaned)


def get_category_fit_policy(
    raw_category: str | None,
    *,
    overrides: dict[str, CategoryFitPolicy] | None = None,
) -> CategoryFitPolicy | None:
    """Return the versioned policy for a category, or None if not registered."""
    code = normalize_category_code(raw_category)
    if overrides and code in overrides:
        return overrides[code]
    return CATEGORY_POLICIES.get(code)
