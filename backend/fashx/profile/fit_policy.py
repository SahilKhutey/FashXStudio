"""Versioned category measurement requirement policies (Phase 08.2 - Task 8.2.1)."""

from __future__ import annotations

from dataclasses import dataclass

FIT_POLICY_VERSION = "1.0"


class UnsupportedCategoryPolicyError(ValueError):
    """Raised when fit policy is requested for an unsupported garment category."""


@dataclass(frozen=True)
class CategoryMeasurementPolicy:
    """Required and optional shopper body measurements for a supported garment category."""

    category: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    policy_version: str
    rationale: str


CATEGORY_POLICIES: dict[str, CategoryMeasurementPolicy] = {
    "TSHIRTS": CategoryMeasurementPolicy(
        category="TSHIRTS",
        required_fields=("CHEST",),
        optional_fields=("SHOULDER", "SLEEVE_LENGTH", "HEIGHT"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Upper-body circumference (chest) anchors T-shirt sizing; shoulder and sleeve refine guidance.",
    ),
    "SHIRTS": CategoryMeasurementPolicy(
        category="SHIRTS",
        required_fields=("CHEST",),
        optional_fields=("NECK", "SHOULDER", "SLEEVE_LENGTH", "HEIGHT"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Chest circumference is essential; collar/neck, shoulder, and sleeve refine formal or tailored shirts.",
    ),
    "KURTAS": CategoryMeasurementPolicy(
        category="KURTAS",
        required_fields=("CHEST",),
        optional_fields=("SHOULDER", "SLEEVE_LENGTH", "WAIST", "HEIGHT"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Chest anchors kurta drape; shoulder, sleeve, waist, and height provide supplementary length context.",
    ),
    "TOPS": CategoryMeasurementPolicy(
        category="TOPS",
        required_fields=("BUST",),
        optional_fields=("WAIST", "SHOULDER", "SLEEVE_LENGTH"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Upper-torso/bust circumference drives top fit; waist and shoulder improve silhouette context.",
    ),
    "TROUSERS": CategoryMeasurementPolicy(
        category="TROUSERS",
        required_fields=("WAIST", "HIP"),
        optional_fields=("INSEAM", "OUTSEAM", "THIGH", "HEIGHT"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Waist and hip circumferences anchor trouser fit; inseam, outseam, and thigh refine leg/length.",
    ),
    "JEANS": CategoryMeasurementPolicy(
        category="JEANS",
        required_fields=("WAIST", "HIP"),
        optional_fields=("INSEAM", "THIGH", "HEIGHT"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Waist and hip govern denim rise and seat fit; inseam and thigh assist leg cut guidance.",
    ),
    "DRESSES": CategoryMeasurementPolicy(
        category="DRESSES",
        required_fields=("BUST", "WAIST", "HIP"),
        optional_fields=("HEIGHT", "SHOULDER"),
        policy_version=FIT_POLICY_VERSION,
        rationale="Dresses require bust, waist, and hip dimensions for three-point upper-to-lower silhouette guidance.",
    ),
    "SKIRTS": CategoryMeasurementPolicy(
        category="SKIRTS",
        required_fields=("WAIST", "HIP"),
        optional_fields=("HEIGHT",),
        policy_version=FIT_POLICY_VERSION,
        rationale="Waistband and hip ease require waist and hip measurements; height informs hemline context.",
    ),
}


@dataclass(frozen=True)
class CategoryReadiness:
    """Readiness state for a single garment category against a shopper's provided fields."""

    category: str
    status: str  # READY | MISSING_REQUIRED_MEASUREMENTS | UNSUPPORTED_CATEGORY
    policy_version: str | None
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    message: str


def get_category_policy(category: str) -> CategoryMeasurementPolicy:
    """Return the versioned policy for a supported category, never falling back across categories."""
    norm = category.strip().upper()
    policy = CATEGORY_POLICIES.get(norm)
    if policy is None:
        raise UnsupportedCategoryPolicyError(
            f"Unsupported fit-profile category '{category}'. Cannot infer requirements from another category."
        )
    return policy


def missing_required_measurements(category: str, provided_fields: set[str]) -> list[str]:
    """Return ordered list of required fields missing for a supported category."""
    policy = get_category_policy(category)
    norm_provided = {f.strip().upper() for f in provided_fields}
    return [f for f in policy.required_fields if f not in norm_provided]


def evaluate_category_readiness(category: str, provided_fields: set[str]) -> CategoryReadiness:
    """Evaluate readiness for a category without blocking general product browsing."""
    norm = category.strip().upper()
    policy = CATEGORY_POLICIES.get(norm)
    if policy is None:
        return CategoryReadiness(
            category=norm,
            status="UNSUPPORTED_CATEGORY",
            policy_version=None,
            required_fields=(),
            optional_fields=(),
            missing_fields=(),
            message=f"Category '{norm}' does not yet have a validated fit policy.",
        )

    missing = tuple(missing_required_measurements(norm, provided_fields))
    if missing:
        return CategoryReadiness(
            category=norm,
            status="MISSING_REQUIRED_MEASUREMENTS",
            policy_version=policy.policy_version,
            required_fields=policy.required_fields,
            optional_fields=policy.optional_fields,
            missing_fields=missing,
            message=f"Add {', '.join(missing)} for future {norm.lower()} fit guidance.",
        )

    return CategoryReadiness(
        category=norm,
        status="READY",
        policy_version=policy.policy_version,
        required_fields=policy.required_fields,
        optional_fields=policy.optional_fields,
        missing_fields=(),
        message=f"All candidate measurements for {norm.lower()} are recorded.",
    )


def evaluate_all_categories_readiness(provided_fields: set[str]) -> dict[str, CategoryReadiness]:
    """Evaluate readiness across every supported garment category."""
    return {
        cat: evaluate_category_readiness(cat, provided_fields) for cat in CATEGORY_POLICIES
    }
