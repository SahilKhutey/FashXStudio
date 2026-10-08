from uuid import uuid4

import pytest

from fashx.core.errors import ConflictError
from fashx.domain.inventory.entities import (
    InventoryItem,
    StockLocation,
    StockMovement,
)
from fashx.domain.inventory.enums import StockAdjustmentType
from fashx.repositories.inventory.memory import (
    InMemoryInventoryRepository,
    InMemoryStockLocationRepository,
    InMemoryStockMovementRepository,
)


@pytest.mark.asyncio
async def test_location_save_get():
    repository = InMemoryStockLocationRepository()

    location = StockLocation(
        name="Main Warehouse",
        code="WH-001",
    )

    await repository.save(location)

    result = await repository.get(location.id)
    assert result is location

    by_code = await repository.get_by_code("wh-001")
    assert by_code is location


@pytest.mark.asyncio
async def test_location_code_conflict():
    repository = InMemoryStockLocationRepository()

    loc1 = StockLocation(
        name="Warehouse 1",
        code="WH-SAME",
    )
    loc2 = StockLocation(
        name="Warehouse 2",
        code="WH-SAME",
    )

    await repository.save(loc1)
    with pytest.raises(ConflictError):
        await repository.save(loc2)


@pytest.mark.asyncio
async def test_inventory_save_get():
    repository = InMemoryInventoryRepository()

    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
    )

    await repository.save(item)

    result = await repository.get(item.id)
    assert result is item


@pytest.mark.asyncio
async def test_inventory_variant_location_conflict():
    repository = InMemoryInventoryRepository()

    variant_id = uuid4()
    location_id = uuid4()

    item1 = InventoryItem(
        variant_id=variant_id,
        location_id=location_id,
    )
    item2 = InventoryItem(
        variant_id=variant_id,
        location_id=location_id,
    )

    await repository.save(item1)
    with pytest.raises(ConflictError):
        await repository.save(item2)


@pytest.mark.asyncio
async def test_variant_inventory_lookup():
    repository = InMemoryInventoryRepository()

    variant_id = uuid4()

    first = InventoryItem(
        variant_id=variant_id,
        location_id=uuid4(),
    )
    second = InventoryItem(
        variant_id=variant_id,
        location_id=uuid4(),
    )

    await repository.save(first)
    await repository.save(second)

    results = await repository.list_by_variant(variant_id)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_stock_movement_save_and_list():
    repository = InMemoryStockMovementRepository()
    inv_id = uuid4()

    mov1 = StockMovement(
        inventory_id=inv_id,
        adjustment_type=StockAdjustmentType.RECEIVE,
        quantity=50,
        reason="Initial batch",
    )
    mov2 = StockMovement(
        inventory_id=inv_id,
        adjustment_type=StockAdjustmentType.DAMAGE,
        quantity=2,
        reason="Broken package",
    )

    await repository.save(mov1)
    await repository.save(mov2)

    movements = await repository.list_by_inventory(inv_id)
    assert len(movements) == 2
