"""Shopper body measurement registry & guidance content (Phase 08.2 - Task 8.2.2)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementDefinition:
    """Defines a body measurement field, shopper instructions, unit rules, and provisional bounds."""

    code: str
    display_name: str
    explanation: str
    tape_positioning: str
    how_to_hold: str
    example_input: str
    measurement_type: str  # CIRCUMFERENCE | LINEAR | WEIGHT
    supported_categories: tuple[str, ...]
    default_unit: str
    minimum_cm: str
    maximum_cm: str
    is_optional_contextual: bool = False


MEASUREMENT_DEFINITIONS: dict[str, MeasurementDefinition] = {
    "CHEST": MeasurementDefinition(
        code="CHEST",
        display_name="Chest",
        explanation=(
            "Measure around the fullest part of your chest. "
            "Keep the tape level and comfortably loose."
        ),
        tape_positioning="Wrap the tape horizontally under your arms and across the fullest part of your chest.",
        how_to_hold="Hold the tape level across your back without pulling it tight; breathe normally.",
        example_input="96.5 cm or 38.0 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("TSHIRTS", "SHIRTS", "KURTAS"),
        default_unit="CM",
        minimum_cm="35",
        maximum_cm="180",
    ),
    "BUST": MeasurementDefinition(
        code="BUST",
        display_name="Bust",
        explanation=(
            "Measure around the fullest part of your bust while keeping the tape level."
        ),
        tape_positioning="Place the tape around the fullest part of your bust and parallel to the floor.",
        how_to_hold="Keep the tape relaxed with one finger of ease so it does not compress.",
        example_input="88.0 cm or 34.5 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("TOPS", "DRESSES"),
        default_unit="CM",
        minimum_cm="35",
        maximum_cm="180",
    ),
    "WAIST": MeasurementDefinition(
        code="WAIST",
        display_name="Waist",
        explanation=(
            "Measure around your natural waist. Keep the tape comfortable, not tight."
        ),
        tape_positioning="Find the natural crease of your torso above your hip bone and wrap the tape around.",
        how_to_hold="Stand relaxed without sucking in; allow comfortable clearance.",
        example_input="78.0 cm or 31.0 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("TOPS", "TROUSERS", "JEANS", "DRESSES", "SKIRTS", "KURTAS"),
        default_unit="CM",
        minimum_cm="30",
        maximum_cm="180",
    ),
    "HIP": MeasurementDefinition(
        code="HIP",
        display_name="Hips",
        explanation="Measure around the fullest part of your hips.",
        tape_positioning="Stand with feet together and wrap the tape around the widest part of your hips and seat.",
        how_to_hold="Ensure the tape stays level around both sides without pinching.",
        example_input="98.0 cm or 38.5 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("TROUSERS", "JEANS", "DRESSES", "SKIRTS"),
        default_unit="CM",
        minimum_cm="35",
        maximum_cm="200",
    ),
    "SHOULDER": MeasurementDefinition(
        code="SHOULDER",
        display_name="Shoulder width",
        explanation="Measure across the back between the outer shoulder points.",
        tape_positioning="Measure from the bony outer edge of one shoulder straight across your upper back to the other.",
        how_to_hold="Keep shoulders relaxed and arms resting naturally at your sides.",
        example_input="44.0 cm or 17.5 in",
        measurement_type="LINEAR",
        supported_categories=("SHIRTS", "TSHIRTS", "KURTAS", "TOPS", "DRESSES"),
        default_unit="CM",
        minimum_cm="20",
        maximum_cm="80",
    ),
    "SLEEVE_LENGTH": MeasurementDefinition(
        code="SLEEVE_LENGTH",
        display_name="Sleeve length",
        explanation="Measure from the shoulder point down the outer arm to your desired sleeve endpoint.",
        tape_positioning="Start at the outer edge of your shoulder and trace slightly curved elbow down to the wrist bone.",
        how_to_hold="Keep your arm slightly relaxed rather than locked stiffly.",
        example_input="62.0 cm or 24.5 in",
        measurement_type="LINEAR",
        supported_categories=("SHIRTS", "TSHIRTS", "KURTAS", "TOPS"),
        default_unit="CM",
        minimum_cm="10",
        maximum_cm="110",
    ),
    "INSEAM": MeasurementDefinition(
        code="INSEAM",
        display_name="Inseam",
        explanation="Measure along the inside of your leg from the crotch point to your desired trouser hem.",
        tape_positioning="Measure straight down the inner leg to the ankle or preferred trouser break.",
        how_to_hold="Stand upright looking straight ahead; wearing well-fitting trousers can help locate the points.",
        example_input="78.0 cm or 30.5 in",
        measurement_type="LINEAR",
        supported_categories=("TROUSERS", "JEANS"),
        default_unit="CM",
        minimum_cm="20",
        maximum_cm="120",
    ),
    "OUTSEAM": MeasurementDefinition(
        code="OUTSEAM",
        display_name="Outseam",
        explanation="Measure along the outside of the leg from your natural waistband level to the trouser hem.",
        tape_positioning="Start on the outer side at waist level and measure down the outer leg to the floor/hem.",
        how_to_hold="Keep the tape vertical without bowing.",
        example_input="102.0 cm or 40.0 in",
        measurement_type="LINEAR",
        supported_categories=("TROUSERS", "JEANS"),
        default_unit="CM",
        minimum_cm="30",
        maximum_cm="160",
    ),
    "THIGH": MeasurementDefinition(
        code="THIGH",
        display_name="Thigh",
        explanation="Measure around the fullest part of your upper thigh.",
        tape_positioning="Wrap the tape horizontally around the widest point of your upper thigh just below the seat.",
        how_to_hold="Keep the tape comfortable and level without pulling tight.",
        example_input="56.0 cm or 22.0 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("TROUSERS", "JEANS"),
        default_unit="CM",
        minimum_cm="20",
        maximum_cm="120",
    ),
    "NECK": MeasurementDefinition(
        code="NECK",
        display_name="Neck",
        explanation="Measure around the base of your neck, allowing comfortable collar clearance.",
        tape_positioning="Place the tape just above your collarbone where a shirt collar naturally sits.",
        how_to_hold="Slide one finger comfortably behind the tape so the collar won't feel restrictive.",
        example_input="39.5 cm or 15.5 in",
        measurement_type="CIRCUMFERENCE",
        supported_categories=("SHIRTS",),
        default_unit="CM",
        minimum_cm="20",
        maximum_cm="70",
    ),
    "HEIGHT": MeasurementDefinition(
        code="HEIGHT",
        display_name="Height",
        explanation="Measure vertically from the floor to the top of your head without shoes.",
        tape_positioning="Stand with heels gently against a wall and mark the crown of your head.",
        how_to_hold="Keep chin level and posture relaxed.",
        example_input="172.0 cm or 67.7 in",
        measurement_type="LINEAR",
        supported_categories=(
            "TSHIRTS",
            "SHIRTS",
            "KURTAS",
            "TOPS",
            "TROUSERS",
            "JEANS",
            "DRESSES",
            "SKIRTS",
        ),
        default_unit="CM",
        minimum_cm="100",
        maximum_cm="230",
        is_optional_contextual=True,
    ),
    "WEIGHT": MeasurementDefinition(
        code="WEIGHT",
        display_name="Weight",
        explanation="Optional contextual data only; never required and not a substitute for body measurements.",
        tape_positioning="Weigh in normal light clothing if you choose to record weight.",
        how_to_hold="Completely optional.",
        example_input="68.0 kg",
        measurement_type="WEIGHT",
        supported_categories=(
            "TSHIRTS",
            "SHIRTS",
            "KURTAS",
            "TOPS",
            "TROUSERS",
            "JEANS",
            "DRESSES",
            "SKIRTS",
        ),
        default_unit="KG",
        minimum_cm="25",
        maximum_cm="300",
        is_optional_contextual=True,
    ),
}


def get_measurement_definition(field_code: str) -> MeasurementDefinition | None:
    """Return measurement definition for a field code, or None if unknown."""
    return MEASUREMENT_DEFINITIONS.get(field_code.strip().upper())


def list_measurement_definitions() -> list[MeasurementDefinition]:
    """List all supported body measurement definitions in stable registry order."""
    return list(MEASUREMENT_DEFINITIONS.values())
