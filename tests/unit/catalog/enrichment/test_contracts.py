from __future__ import annotations

import pytest
from pydantic import ValidationError

from fashx.catalog.enrichment.contracts import (
    AttributeResult,
    AttributeStatus,
    EnrichmentInput,
    EnrichmentOutput,
    ProductContent,
    ReviewStatus,
)


def test_enr_001_valid_enrichment_input() -> None:
    """Verify ENR-001: Valid enrichment input is accepted."""
    inp = EnrichmentInput(
        product_id="prod-123",
        merchant_id="merch-456",
        source_id="src-789",
        source_product_id="sku-001",
        taxonomy_version="1.0.0",
        content=ProductContent(
            title="Men's Regular Fit Cotton Navy Blue Shirt",
            description="Casual regular fit button down shirt.",
            merchant_category="Men > Clothing > Shirts",
        ),
    )
    assert inp.product_id == "prod-123"
    assert inp.text_processing_allowed is True
    assert inp.image_ai_processing_allowed is False


def test_enr_002_missing_product_id_rejected() -> None:
    """Verify ENR-002: Missing or blank product_id is rejected."""
    with pytest.raises(ValidationError):
        EnrichmentInput(
            product_id="",
            merchant_id="merch-456",
            source_id="src-789",
            source_product_id="sku-001",
            taxonomy_version="1.0.0",
            content=ProductContent(title="Valid Title"),
        )


def test_enr_003_missing_taxonomy_version_rejected() -> None:
    """Verify ENR-003: Missing or blank taxonomy_version is rejected."""
    with pytest.raises(ValidationError):
        EnrichmentInput(
            product_id="prod-123",
            merchant_id="merch-456",
            source_id="src-789",
            source_product_id="sku-001",
            taxonomy_version="",
            content=ProductContent(title="Valid Title"),
        )


def test_enr_004_empty_product_title_rejected() -> None:
    """Verify ENR-004: Empty or whitespace-only product title is rejected."""
    with pytest.raises(ValidationError):
        ProductContent(title="   ")


def test_known_attribute_requires_value() -> None:
    """Verify that an attribute with status KNOWN requires a non-null value."""
    with pytest.raises(ValidationError):
        AttributeResult(
            value=None,
            status=AttributeStatus.KNOWN,
            review_status=ReviewStatus.PENDING_REVIEW,
        )


def test_unknown_attribute_cannot_have_value() -> None:
    """Verify that an attribute with status UNKNOWN cannot have a non-null value."""
    with pytest.raises(ValidationError):
        AttributeResult(
            value="cotton",
            status=AttributeStatus.UNKNOWN,
            review_status=ReviewStatus.NOT_REQUIRED,
        )


def test_confidence_requires_source() -> None:
    """Verify that providing a confidence score requires an explicit source."""
    with pytest.raises(ValidationError):
        AttributeResult(
            value="navy",
            status=AttributeStatus.KNOWN,
            confidence=0.95,
            source=None,
        )


def test_enr_022_ai_output_contains_unknown_field_rejected() -> None:
    """Verify ENR-022: Unexpected extra fields in output contract are strictly forbidden."""
    with pytest.raises(ValidationError):
        EnrichmentOutput.model_validate(
            {
                "schema_version": "1.0.0",
                "product_id": "prod-123",
                "taxonomy_version": "1.0.0",
                "enrichment_version": "1.0.0",
                "status": "COMPLETED",
                "unexpected_field": "injected_payload",
            }
        )
