from __future__ import annotations

import pytest

from fashx.catalog.taxonomy.contracts import (
    AttributeSource,
    FabricSpecification,
    IndianWearAttributes,
    MaterialBlendItem,
    ProductClassification,
    TaxonomyAttributeValue,
    ValueStatus,
    WesternWearAttributes,
)
from fashx.catalog.taxonomy.loader import get_taxonomy_registry
from fashx.catalog.taxonomy.validator import TaxonomyValidationError, TaxonomyValidator


@pytest.fixture
def validator() -> TaxonomyValidator:
    return TaxonomyValidator(get_taxonomy_registry())


def test_valid_t_shirt_classification_passes(validator: TaxonomyValidator) -> None:
    """Verify standard valid T-shirt passes taxonomy validation."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="apparel_tops_t_shirts",
        garment_type_id="t_shirt",
        style_family="western",
        intended_audience="men",
        occasions=["casual", "everyday"],
        attributes={
            "color": TaxonomyAttributeValue(
                attribute_id="color", value="navy", status=ValueStatus.KNOWN, source=AttributeSource.MERCHANT
            ),
            "pattern": TaxonomyAttributeValue(
                attribute_id="pattern", value="solid", status=ValueStatus.KNOWN, source=AttributeSource.MERCHANT
            ),
            "material": TaxonomyAttributeValue(
                attribute_id="material", value="cotton", status=ValueStatus.KNOWN, source=AttributeSource.MERCHANT
            ),
            "sleeve_type": TaxonomyAttributeValue(
                attribute_id="sleeve_type", value="short_sleeve", status=ValueStatus.KNOWN
            ),
            "neckline": TaxonomyAttributeValue(
                attribute_id="neckline", value="crew_neck", status=ValueStatus.KNOWN
            ),
            "fit": TaxonomyAttributeValue(
                attribute_id="fit", value="regular", status=ValueStatus.KNOWN
            ),
        },
        western_wear=WesternWearAttributes(t_shirt_type="crew_neck"),
    )
    # Must not raise
    validator.validate(item)


def test_valid_kurta_classification_passes(validator: TaxonomyValidator) -> None:
    """Verify TAX-011: Indian wear kurta with craft techniques passes validation."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="ethnic_wear_kurtas_and_kurtis",
        garment_type_id="kurta",
        style_family="indian_ethnic",
        intended_audience="men",
        occasions=["festive", "traditional_ceremony"],
        attributes={
            "color": TaxonomyAttributeValue(
                attribute_id="color", value="ivory", status=ValueStatus.KNOWN
            ),
            "material": TaxonomyAttributeValue(
                attribute_id="material", value="silk", status=ValueStatus.KNOWN
            ),
            "sleeve_type": TaxonomyAttributeValue(
                attribute_id="sleeve_type", value="full_sleeve", status=ValueStatus.KNOWN
            ),
            "neckline": TaxonomyAttributeValue(
                attribute_id="neckline", value="mandarin_collar", status=ValueStatus.KNOWN
            ),
        },
        indian_wear=IndianWearAttributes(
            ethnic_garment_type="kurta",
            kurta_length="knee",
            kurta_style="straight",
            craft_technique=["chikankari"],
            embellishments=["embroidery"],
        ),
    )
    validator.validate(item)


def test_invalid_taxonomy_version_rejected(validator: TaxonomyValidator) -> None:
    """Verify version mismatch raises error."""
    item = ProductClassification(
        taxonomy_version="9.9.9",
        category_id="apparel_tops_t_shirts",
    )
    with pytest.raises(TaxonomyValidationError, match="Taxonomy version mismatch"):
        validator.validate(item)


def test_non_leaf_category_rejected(validator: TaxonomyValidator) -> None:
    """Verify non-leaf root category rejected for product classification."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="apparel",  # root, not leaf
    )
    with pytest.raises(TaxonomyValidationError, match="not a leaf category"):
        validator.validate(item, enforce_leaf=True)


def test_incompatible_garment_type_rejected(validator: TaxonomyValidator) -> None:
    """Verify incompatible garment type in category is rejected."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="apparel_tops_t_shirts",
        garment_type_id="kurta",  # Kurta is ethnic wear, not apparel tops
    )
    with pytest.raises(TaxonomyValidationError, match="is incompatible with category"):
        validator.validate(item)


def test_inapplicable_attribute_rejected(validator: TaxonomyValidator) -> None:
    """Verify TAX-014: neckline attribute rejected on accessories / bags."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="accessories_bags",
        garment_type_id="handbag",
        attributes={
            "neckline": TaxonomyAttributeValue(
                attribute_id="neckline",
                value="crew_neck",
                status=ValueStatus.KNOWN,
            )
        },
    )
    with pytest.raises(TaxonomyValidationError, match="is NOT APPLICABLE"):
        validator.validate(item)


def test_inapplicable_attribute_marked_not_applicable_accepted(validator: TaxonomyValidator) -> None:
    """Verify attribute marked NOT_APPLICABLE with null value is permitted."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="accessories_bags",
        garment_type_id="handbag",
        attributes={
            "neckline": TaxonomyAttributeValue(
                attribute_id="neckline",
                value=None,
                status=ValueStatus.NOT_APPLICABLE,
            )
        },
    )
    validator.validate(item)


def test_invalid_color_or_material_rejected(validator: TaxonomyValidator) -> None:
    """Verify invalid controlled values are rejected."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="apparel_tops_t_shirts",
        attributes={
            "color": TaxonomyAttributeValue(
                attribute_id="color",
                value="uninvented_radioactive_glow",
                status=ValueStatus.KNOWN,
            )
        },
    )
    with pytest.raises(TaxonomyValidationError, match="Invalid color value"):
        validator.validate(item)


def test_fabric_blend_percentage_validation() -> None:
    """Verify TAX-008: fabric blend percentages sum to 100 within tolerance."""
    # Valid 80/20 cotton polyester
    valid_spec = FabricSpecification(
        materials=[
            MaterialBlendItem(material="cotton", percentage=80.0),
            MaterialBlendItem(material="polyester", percentage=20.0),
        ]
    )
    assert len(valid_spec.materials) == 2

    # Invalid: sums to 110%
    with pytest.raises(ValueError, match="percentages must sum to ~100%"):
        FabricSpecification(
            materials=[
                MaterialBlendItem(material="cotton", percentage=80.0),
                MaterialBlendItem(material="polyester", percentage=30.0),
            ]
        )


def test_category_extension_mismatch_rejected(validator: TaxonomyValidator) -> None:
    """Verify Indian wear attributes on sneakers are rejected."""
    item = ProductClassification(
        taxonomy_version="1.0.0",
        category_id="footwear_sneakers",
        garment_type_id="sneakers",
        indian_wear=IndianWearAttributes(kurta_length="knee"),
    )
    with pytest.raises(TaxonomyValidationError, match="Indian wear attributes cannot be attached"):
        validator.validate(item)
