from __future__ import annotations

import pytest

from fashx.catalog.taxonomy.versioning import SemanticVersion, TaxonomyVersionManager


def test_semantic_version_parsing_and_compatibility() -> None:
    """Verify TAX-015: Semantic versioning and backward-compatibility rules."""
    v1_0_0 = SemanticVersion.parse("1.0.0")
    v1_1_0 = SemanticVersion.parse("1.1.0")
    v2_0_0 = SemanticVersion.parse("2.0.0")

    # Registry at 1.1.0 is compatible with product at 1.0.0 (backward compatible)
    assert v1_1_0.is_compatible_with(v1_0_0)
    assert v1_0_0.is_compatible_with(v1_0_0)

    # Registry at 1.0.0 is NOT compatible with product at 1.1.0 (needs newer registry features)
    assert not v1_0_0.is_compatible_with(v1_1_0)

    # Major version jump is breaking
    assert not v2_0_0.is_compatible_with(v1_0_0)
    assert not v1_1_0.is_compatible_with(v2_0_0)


def test_invalid_semantic_version_format() -> None:
    with pytest.raises(ValueError, match="Invalid semantic version format"):
        SemanticVersion.parse("v1.0")


def test_taxonomy_deprecation_lifecycle() -> None:
    """Verify registration and lookup of deprecated taxonomy items."""
    manager = TaxonomyVersionManager(active_version="1.0.0")

    manager.register_deprecation(
        item_type="category",
        item_id="legacy_tops",
        deprecated_in="1.0.0",
        effective_sunset="2.0.0",
        replacement_id="apparel_tops",
        reason="Consolidated into hierarchical apparel_tops",
    )

    assert manager.is_deprecated("category", "legacy_tops")
    record = manager.get_deprecation("category", "legacy_tops")
    assert record is not None
    assert record.replacement_id == "apparel_tops"
    assert not manager.is_deprecated("category", "apparel_tops")
