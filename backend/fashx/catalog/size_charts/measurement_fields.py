"""Garment-specific measurement field registry and boundary definitions for Phase 08.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementFieldDefinition:
    """Defines an approved linear measurement field and its category eligibility."""

    code: str
    display_name: str
    allowed_categories: tuple[str, ...]
    minimum_cm: float
    maximum_cm: float
    description: str | None = None


FIELD_DEFINITIONS: dict[str, MeasurementFieldDefinition] = {
    "CHEST": MeasurementFieldDefinition(
        code="CHEST",
        display_name="Chest",
        allowed_categories=("TSHIRTS", "SHIRTS", "KURTAS", "CASUAL_SHIRTS", "FORMAL_SHIRTS", "TOPS", "DRESSES", "OUTERWEAR", "GENERAL"),
        minimum_cm=40.0,
        maximum_cm=200.0,
        description="Chest circumference or width across chest under armpits.",
    ),
    "BUST": MeasurementFieldDefinition(
        code="BUST",
        display_name="Bust",
        allowed_categories=("TOPS", "DRESSES", "KURTAS", "WESTERN_WEAR", "GENERAL"),
        minimum_cm=40.0,
        maximum_cm=200.0,
        description="Bust circumference around fullest part or garment chest width.",
    ),
    "WAIST": MeasurementFieldDefinition(
        code="WAIST",
        display_name="Waist",
        allowed_categories=("TOPS", "TROUSERS", "JEANS", "DRESSES", "SKIRTS", "BOTTOMS", "KURTAS", "GENERAL"),
        minimum_cm=30.0,
        maximum_cm=180.0,
        description="Waist circumference or relaxed/stretched waistband width.",
    ),
    "HIP": MeasurementFieldDefinition(
        code="HIP",
        display_name="Hip",
        allowed_categories=("TROUSERS", "JEANS", "DRESSES", "SKIRTS", "BOTTOMS", "KURTAS", "GENERAL"),
        minimum_cm=40.0,
        maximum_cm=220.0,
        description="Hip circumference around fullest part of hips.",
    ),
    "LENGTH": MeasurementFieldDefinition(
        code="LENGTH",
        display_name="Length",
        allowed_categories=("TSHIRTS", "SHIRTS", "KURTAS", "TOPS", "DRESSES", "SKIRTS", "CASUAL_SHIRTS", "FORMAL_SHIRTS", "BOTTOMS", "TROUSERS", "JEANS", "GENERAL", "ALL"),
        minimum_cm=15.0,
        maximum_cm=250.0,
        description="Garment total length from high point shoulder to hem.",
    ),
    "SHOULDER": MeasurementFieldDefinition(
        code="SHOULDER",
        display_name="Shoulder",
        allowed_categories=("TSHIRTS", "SHIRTS", "KURTAS", "TOPS", "DRESSES", "CASUAL_SHIRTS", "FORMAL_SHIRTS", "OUTERWEAR", "GENERAL"),
        minimum_cm=20.0,
        maximum_cm=80.0,
        description="Shoulder width seam-to-seam across back.",
    ),
    "SLEEVE_LENGTH": MeasurementFieldDefinition(
        code="SLEEVE_LENGTH",
        display_name="Sleeve Length",
        allowed_categories=("TSHIRTS", "SHIRTS", "KURTAS", "TOPS", "DRESSES", "OUTERWEAR", "GENERAL"),
        minimum_cm=10.0,
        maximum_cm=110.0,
        description="Sleeve length from shoulder seam to wrist/cuff.",
    ),
    "INSEAM": MeasurementFieldDefinition(
        code="INSEAM",
        display_name="Inseam",
        allowed_categories=("TROUSERS", "JEANS", "BOTTOMS", "SHORTS"),
        minimum_cm=20.0,
        maximum_cm=120.0,
        description="Inner leg seam length from crotch point to bottom hem.",
    ),
    "OUTSEAM": MeasurementFieldDefinition(
        code="OUTSEAM",
        display_name="Outseam",
        allowed_categories=("TROUSERS", "JEANS", "BOTTOMS", "SHORTS"),
        minimum_cm=30.0,
        maximum_cm=160.0,
        description="Outer leg seam length from waistband top to hem.",
    ),
    "THIGH": MeasurementFieldDefinition(
        code="THIGH",
        display_name="Thigh",
        allowed_categories=("TROUSERS", "JEANS", "BOTTOMS", "SHORTS"),
        minimum_cm=20.0,
        maximum_cm=120.0,
        description="Thigh circumference around fullest part of upper leg.",
    ),
    "RISE": MeasurementFieldDefinition(
        code="RISE",
        display_name="Rise",
        allowed_categories=("TROUSERS", "JEANS", "BOTTOMS", "SHORTS"),
        minimum_cm=15.0,
        maximum_cm=60.0,
        description="Distance from crotch seam to top of waistband.",
    ),
    "NECK": MeasurementFieldDefinition(
        code="NECK",
        display_name="Neck",
        allowed_categories=("SHIRTS", "FORMAL_SHIRTS", "CASUAL_SHIRTS", "TOPS", "KURTAS"),
        minimum_cm=25.0,
        maximum_cm=65.0,
        description="Collar/neck circumference.",
    ),
}


def get_field_definition(code: str) -> MeasurementFieldDefinition | None:
    """Retrieve definition for a field code."""
    return FIELD_DEFINITIONS.get(code.upper())


def is_field_valid_for_category(code: str, category: str) -> bool:
    """Check if a measurement field is valid for a given category."""
    defn = get_field_definition(code)
    if defn is None:
        return False
    cat = category.upper()
    if "ALL" in defn.allowed_categories or "GENERAL" in defn.allowed_categories and cat == "GENERAL":
        return True
    return cat in defn.allowed_categories
