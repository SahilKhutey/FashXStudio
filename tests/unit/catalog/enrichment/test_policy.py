from __future__ import annotations

import pytest

from fashx.catalog.enrichment.policy import (
    EnrichmentPolicyError,
    validate_fabric_claim,
    validate_model_attributes,
    validate_size_claim,
)


def test_enr_016_model_cannot_generate_available_sizes() -> None:
    """Verify ENR-016: AI model output cannot invent available sizes."""
    with pytest.raises(EnrichmentPolicyError, match="Model attempted to provide source-only fields"):
        validate_model_attributes({"available_sizes": ["S", "M", "L"]})


def test_model_cannot_generate_size_chart() -> None:
    """Verify that AI models cannot generate size charts or measurements."""
    with pytest.raises(EnrichmentPolicyError, match="Model attempted to provide source-only fields"):
        validate_model_attributes({"size_chart": {"M": {"chest": 38}}})

    with pytest.raises(EnrichmentPolicyError, match="Model attempted to provide source-only fields"):
        validate_model_attributes({"garment_measurements": {"length": 28}})


def test_enr_017_model_cannot_generate_fabric_percentages() -> None:
    """Verify ENR-017: AI models cannot invent fabric composition percentages."""
    with pytest.raises(EnrichmentPolicyError, match="Model attempted to provide source-only fields"):
        validate_model_attributes({
            "fabric_composition_percentages": {"cotton": 80, "polyester": 20}
        })


def test_enr_014_image_only_fabric_inference_rejected() -> None:
    """Verify ENR-014: Fabric claims inferred from images alone are strictly rejected."""
    with pytest.raises(EnrichmentPolicyError, match="Fabric claims cannot be inferred from product images alone"):
        validate_fabric_claim("fabric", "silk", evidence_present=True, evidence_type="IMAGE_ASSET")


def test_fabric_without_evidence_rejected() -> None:
    """Verify that fabric attributes require explicit evidence presence."""
    with pytest.raises(EnrichmentPolicyError, match="requires explicit source evidence"):
        validate_fabric_claim("fabric", "cotton", evidence_present=False)


def test_size_claim_from_ai_source_rejected() -> None:
    """Verify that size attributes originating from AI text/image sources are blocked."""
    with pytest.raises(EnrichmentPolicyError, match="cannot be inferred by AI"):
        validate_size_claim("available_sizes", ["S", "M"], source_type="AI_TEXT")
