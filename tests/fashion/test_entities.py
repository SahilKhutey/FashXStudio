import pytest

from app.core.errors import ValidationError
from app.domain.fashion.entities import (
    FashionAttribute,
    ProductFashionProfile,
    TaxonomyNode,
)
from app.domain.fashion.enums import (
    ClassificationSource,
    TaxonomyType,
)


def test_taxonomy_node_validates():
    node = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
    )

    node.validate()


def test_taxonomy_requires_name():
    node = TaxonomyNode(
        name="",
        slug="shirt",
    )

    with pytest.raises(ValidationError):
        node.validate()


def test_taxonomy_requires_slug():
    node = TaxonomyNode(
        name="Shirt",
        slug="",
    )

    with pytest.raises(ValidationError):
        node.validate()


def test_attribute_validation():
    attribute = FashionAttribute(
        key="color",
        value="black",
    )

    attribute.validate()


def test_profile_requires_product():
    profile = ProductFashionProfile(
        source=ClassificationSource.MANUAL
    )

    with pytest.raises(ValidationError):
        profile.validate()


def test_profile_confidence_range():
    from app.core.ids import new_id

    profile = ProductFashionProfile(
        product_id=new_id(),
        confidence=1.5,
    )

    with pytest.raises(ValidationError):
        profile.validate()
