from __future__ import annotations

from typing import Any

from fashx.catalog.taxonomy.registry import TaxonomyRegistry

from .contracts import AttributeResult, AttributeStatus, ReviewFlag
from .policy import validate_fabric_claim, validate_model_attributes, validate_size_claim


class EnrichmentValidationError(ValueError):
    """Raised when an attribute value violates taxonomy vocabulary or applicability rules."""


def validate_enrichment_attributes(
    attributes: dict[str, AttributeResult],
    registry: TaxonomyRegistry,
    category_id: str | None,
) -> list[str]:
    """Validate all extracted attributes against Phase 6.1 taxonomy vocabulary and rules.

    Returns a list of validation failure reasons if any are detected.
    """
    errors: list[str] = []

    # 1. First validate model attributes against data integrity policy
    raw_dict: dict[str, Any] = {
        k: v.value for k, v in attributes.items() if v.status == AttributeStatus.KNOWN
    }
    try:
        validate_model_attributes(raw_dict)
    except Exception as e:
        errors.append(str(e))

    for attr_id, res in attributes.items():
        # Check source-only size protection
        try:
            validate_size_claim(attr_id, res.value, res.source.value if res.source else None)
        except Exception as e:
            errors.append(str(e))

        # Check fabric evidence requirement
        if attr_id in {"fabric", "fabric_blend", "fabric_composition"}:
            evidence_present = len(res.evidence_ids) > 0
            try:
                validate_fabric_claim(attr_id, res.value, evidence_present)
            except Exception as e:
                errors.append(str(e))

        # Only validate vocabulary for KNOWN values
        if res.status != AttributeStatus.KNOWN or res.value is None:
            continue

        val = str(res.value)

        # 2. Check if attribute is applicable to category
        if category_id is not None:
            if not registry.is_attribute_applicable(category_id, attr_id):
                errors.append(
                    f"Attribute '{attr_id}' is not applicable to category '{category_id}'"
                )
                res.flags.append(ReviewFlag.UNSUPPORTED_ATTRIBUTE)

        # 3. Vocabulary checks
        if attr_id == "color":
            if not registry.is_valid_color(val):
                # Check alias
                resolved = registry.resolve_alias("color", val)
                if not resolved:
                    errors.append(f"Invalid color value '{val}' not found in taxonomy vocabulary")
                    res.flags.append(ReviewFlag.INVALID_TAXONOMY_VALUE)
        elif attr_id == "pattern":
            if not registry.is_valid_pattern(val):
                resolved = registry.resolve_alias("pattern", val)
                if not resolved:
                    errors.append(f"Invalid pattern value '{val}' not found in taxonomy vocabulary")
                    res.flags.append(ReviewFlag.INVALID_TAXONOMY_VALUE)
        elif attr_id == "fabric":
            if not registry.is_valid_fabric(val):
                resolved = registry.resolve_alias("fabric", val)
                if not resolved:
                    errors.append(f"Invalid fabric value '{val}' not found in taxonomy vocabulary")
                    res.flags.append(ReviewFlag.INVALID_TAXONOMY_VALUE)
        elif attr_id == "fit_type":
            if not registry.is_valid_silhouette(val):
                resolved = registry.resolve_alias("silhouette", val)
                if not resolved:
                    errors.append(f"Invalid fit value '{val}' not found in taxonomy vocabulary")
                    res.flags.append(ReviewFlag.INVALID_TAXONOMY_VALUE)
        elif attr_id == "occasion":
            if not registry.is_valid_occasion(val):
                resolved = registry.resolve_alias("occasion", val)
                if not resolved:
                    errors.append(f"Invalid occasion value '{val}' not found in taxonomy vocabulary")
                    res.flags.append(ReviewFlag.INVALID_TAXONOMY_VALUE)

    return errors
