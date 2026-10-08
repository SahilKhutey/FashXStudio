import pytest

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus
from app.core.ids import new_id
from app.domain.fashion.entities import (
    FashionAttribute,
    TaxonomyNode,
)
from app.domain.fashion.enums import (
    ClassificationSource,
    TaxonomyType,
)
from app.domain.fashion.service import FashionService
from fashx.repositories.fashion.memory import (
    InMemoryProductFashionRepository,
    InMemoryTaxonomyRepository,
)


@pytest.fixture
def service():
    return FashionService(
        taxonomy_repository=InMemoryTaxonomyRepository(),
        classification_repository=(
            InMemoryProductFashionRepository()
        ),
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_classify_product(service):
    node = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
    )

    await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=node,
    )

    product_id = new_id()

    profile = await service.classify_product(
        context=CoreContext.create(),
        product_id=product_id,
        taxonomy_node_ids={node.id},
        attributes=[
            FashionAttribute(
                key="fit",
                value="oversized",
            )
        ],
        source=ClassificationSource.MANUAL,
    )

    assert profile.product_id == product_id
    assert node.id in profile.taxonomy_node_ids
    assert profile.attributes[0].value == "oversized"


@pytest.mark.asyncio
async def test_unknown_taxonomy_rejected(service):
    with pytest.raises(NotFoundError):
        await service.classify_product(
            context=CoreContext.create(),
            product_id=new_id(),
            taxonomy_node_ids={new_id()},
            attributes=[],
            source=ClassificationSource.MANUAL,
        )


@pytest.mark.asyncio
async def test_get_classification(service):
    product_id = new_id()

    node = TaxonomyNode(
        name="Casual",
        slug="casual",
        taxonomy_type=TaxonomyType.STYLE,
    )

    await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=node,
    )

    await service.classify_product(
        context=CoreContext.create(),
        product_id=product_id,
        taxonomy_node_ids={node.id},
        attributes=[],
        source=ClassificationSource.MANUAL,
    )

    profile = await service.get_product_classification(
        product_id
    )

    assert profile.product_id == product_id
