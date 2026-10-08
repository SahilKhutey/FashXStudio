import pytest

from app.core.ids import new_id
from fashx.domain.fashion.entities import (
    ProductFashionProfile,
    TaxonomyNode,
)
from fashx.domain.fashion.enums import TaxonomyType
from fashx.repositories.fashion.memory import (
    InMemoryProductFashionRepository,
    InMemoryTaxonomyRepository,
)


@pytest.mark.asyncio
async def test_taxonomy_save_and_get():
    repository = InMemoryTaxonomyRepository()

    node = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
    )

    await repository.save(node)

    result = await repository.get(node.id)

    assert result is node


@pytest.mark.asyncio
async def test_taxonomy_slug_unique():
    repository = InMemoryTaxonomyRepository()

    first = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
    )

    second = TaxonomyNode(
        name="Another Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
    )

    await repository.save(first)

    from app.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await repository.save(second)


@pytest.mark.asyncio
async def test_product_profile_save():
    repository = InMemoryProductFashionRepository()

    product_id = new_id()

    profile = ProductFashionProfile(
        product_id=product_id
    )

    await repository.save(profile)

    result = await repository.get_by_product(
        product_id
    )

    assert result is profile
