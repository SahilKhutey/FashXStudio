import pytest

from fashx.core.errors import ConflictError
from fashx.domain.commerce.entities import (
    Brand,
    Seller,
)
from fashx.repositories.commerce.memory import (
    InMemoryBrandRepository,
    InMemorySellerRepository,
)


@pytest.mark.asyncio
async def test_brand_save_and_get():

    repository = InMemoryBrandRepository()

    brand = Brand(
        name="FashX",
        slug="fashx",
    )

    await repository.save(brand)

    result = await repository.get(brand.id)

    assert result is brand


@pytest.mark.asyncio
async def test_brand_slug_is_unique():

    repository = InMemoryBrandRepository()

    first = Brand(
        name="Brand A",
        slug="brand",
    )

    second = Brand(
        name="Brand B",
        slug="brand",
    )

    await repository.save(first)

    with pytest.raises(ConflictError):
        await repository.save(second)


@pytest.mark.asyncio
async def test_seller_slug_is_unique():

    repository = InMemorySellerRepository()

    first = Seller(
        name="Seller A",
        slug="seller",
    )

    second = Seller(
        name="Seller B",
        slug="seller",
    )

    await repository.save(first)

    with pytest.raises(ConflictError):
        await repository.save(second)
