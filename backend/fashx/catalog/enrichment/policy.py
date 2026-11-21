from __future__ import annotations

from typing import Any

SOURCE_ONLY_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "available_sizes",
        "size_chart",
        "garment_measurements",
        "body_measurements",
        "price",
        "stock_quantity",
        "fabric_composition_percentages",
        "certifications",
        "sustainability_certifications",
        "care_instructions",
    }
)

FABRIC_EVIDENCE_REQUIRED: frozenset[str] = frozenset(
    {
        "fabric",
        "fabric_blend",
        "fabric_composition",
        "fabric_composition_percentages",
    }
)

AI_ALLOWED_INFERENCES: frozenset[str] = frozenset(
    {
        "garment_type",
        "category",
        "color",
        "pattern",
        "style_family",
        "style_descriptors",
        "occasion",
        "fit_type",
        "silhouette",
        "neckline",
        "sleeve_type",
    }
)


class EnrichmentPolicyError(ValueError):
    """Raised when an enrichment step or AI model violates catalog data integrity policy."""


def validate_model_attributes(model_attributes: dict[str, Any]) -> None:
    """Validate that an AI model output does not attempt to supply source-only or forbidden fields."""
    keys = set(model_attributes.keys())
    prohibited = SOURCE_ONLY_ATTRIBUTES.intersection(keys)
    if prohibited:
        raise EnrichmentPolicyError(
            f"Model attempted to provide source-only fields: {sorted(prohibited)}"
        )


def validate_fabric_claim(
    attribute_id: str,
    value: Any,
    evidence_present: bool,
    evidence_type: str | None = None,
) -> None:
    """Validate that fabric claims comply with the strict source-evidence rule (Section 6.2.7)."""
    if evidence_type in {"IMAGE_ASSET", "AI_IMAGE_EXTRACTION"}:
        raise EnrichmentPolicyError(
            "Fabric claims cannot be inferred from product images alone (Rule 6.2.7 / ENR-014)"
        )

    if attribute_id in FABRIC_EVIDENCE_REQUIRED:
        if not evidence_present or value is None:
            raise EnrichmentPolicyError(
                f"Fabric attribute {attribute_id} requires explicit source evidence (Rule 6.2.7)"
            )


def validate_size_claim(attribute_id: str, value: Any, source_type: str | None) -> None:
    """Validate that size attributes originate strictly from source data, never AI inference."""
    if attribute_id in {
        "available_sizes",
        "size_chart",
        "garment_measurements",
        "body_measurements",
    }:
        if source_type in {"AI_TEXT", "AI_IMAGE", "AI_TEXT_EXTRACTION", "AI_IMAGE_EXTRACTION"}:
            raise EnrichmentPolicyError(
                f"Size attribute {attribute_id} cannot be inferred by AI (Rule 6.2.15 / ENR-016)"
            )
