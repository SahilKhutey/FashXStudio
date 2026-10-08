import pytest

from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.event_bus import EventBus
from fashx.domain.fashion.entities import TaxonomyNode
from fashx.domain.fashion.enums import TaxonomyType
from fashx.domain.fashion.service import FashionService
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
async def test_create_root_taxonomy(service):
    node = TaxonomyNode(
        name="Apparel",
        slug="apparel",
        taxonomy_type=TaxonomyType.CATEGORY,
    )

    result = await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=node,
    )

    assert result.id == node.id


@pytest.mark.asyncio
async def test_missing_parent_rejected(service):
    from app.core.ids import new_id

    node = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
        parent_id=new_id(),
    )

    with pytest.raises(NotFoundError):
        await service.create_taxonomy_node(
            context=CoreContext.create(),
            node=node,
        )


@pytest.mark.asyncio
async def test_children_are_returned(service):
    parent = TaxonomyNode(
        name="Tops",
        slug="tops",
        taxonomy_type=TaxonomyType.SUBCATEGORY,
    )

    await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=parent,
    )

    child = TaxonomyNode(
        name="Shirt",
        slug="shirt",
        taxonomy_type=TaxonomyType.GARMENT,
        parent_id=parent.id,
    )

    await service.create_taxonomy_node(
        context=CoreContext.create(),
        node=child,
    )

    children = await service.list_children(parent.id)

    assert len(children) == 1
    assert children[0].slug == "shirt"
