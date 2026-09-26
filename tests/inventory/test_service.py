from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.event_bus import EventBus
from app.domain.inventory.entities import (
    InventoryItem,
    StockLocation,
)
from app.domain.inventory.enums import (
    InventoryStatus,
    StockAdjustmentType,
)
from app.domain.inventory.service import (
    InventoryService,
)
from app.repositories.inventory.memory import (
    InMemoryInventoryRepository,
    InMemoryStockLocationRepository,
    InMemoryStockMovementRepository,
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def service(event_bus):
    return InventoryService(
        inventory_repository=InMemoryInventoryRepository(),
        location_repository=InMemoryStockLocationRepository(),
        movement_repository=InMemoryStockMovementRepository(),
        event_bus=event_bus,
    )


@pytest.mark.asyncio
async def test_create_location(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("StockLocationCreated", handler)

    loc = StockLocation(name="Warehouse A", code="WH-A")
    res = await service.create_location(
        context=CoreContext.create(),
        location=loc,
    )

    assert res.name == "Warehouse A"
    assert len(events) == 1
    assert events[0].entity_id == loc.id


@pytest.mark.asyncio
async def test_create_inventory(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("InventoryCreated", handler)

    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(
            name="Warehouse A",
            code="WH-A",
        ),
    )

    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=100,
        ),
    )

    assert item.on_hand == 100
    assert item.available == 100
    assert len(events) == 1
    assert events[0].entity_id == item.id


@pytest.mark.asyncio
async def test_create_inventory_location_not_found(service):
    with pytest.raises(NotFoundError):
        await service.create_inventory(
            context=CoreContext.create(),
            inventory=InventoryItem(
                variant_id=uuid4(),
                location_id=uuid4(),
                status=InventoryStatus.ACTIVE,
                on_hand=100,
            ),
        )


@pytest.mark.asyncio
async def test_create_inventory_conflict(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-01"),
    )
    variant_id = uuid4()
    item1 = InventoryItem(
        variant_id=variant_id,
        location_id=location.id,
    )
    item2 = InventoryItem(
        variant_id=variant_id,
        location_id=location.id,
    )

    await service.create_inventory(
        context=CoreContext.create(),
        inventory=item1,
    )
    with pytest.raises(ConflictError):
        await service.create_inventory(
            context=CoreContext.create(),
            inventory=item2,
        )


@pytest.mark.asyncio
async def test_receive_stock(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("InventoryAdjusted", handler)

    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(
            name="Warehouse A",
            code="WH-A",
        ),
    )

    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=100,
        ),
    )

    result = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=item.id,
        adjustment_type=StockAdjustmentType.RECEIVE,
        quantity=50,
        reason="Inbound shipment",
    )

    assert result.on_hand == 150
    assert result.available == 150
    assert len(events) == 1


@pytest.mark.asyncio
async def test_add_stock(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-ADD"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=50,
        ),
    )
    result = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=item.id,
        adjustment_type=StockAdjustmentType.ADD,
        quantity=25,
    )
    assert result.on_hand == 75


@pytest.mark.asyncio
async def test_remove_stock(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(
            name="Warehouse A",
            code="WH-A",
        ),
    )

    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=100,
        ),
    )

    result = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=item.id,
        adjustment_type=StockAdjustmentType.REMOVE,
        quantity=30,
    )

    assert result.on_hand == 70
    assert result.available == 70


@pytest.mark.asyncio
async def test_damage_and_loss(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-DMG"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=100,
        ),
    )
    res_dmg = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=item.id,
        adjustment_type=StockAdjustmentType.DAMAGE,
        quantity=5,
    )
    assert res_dmg.on_hand == 95

    res_loss = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=item.id,
        adjustment_type=StockAdjustmentType.LOSS,
        quantity=10,
    )
    assert res_loss.on_hand == 85


@pytest.mark.asyncio
async def test_overselling_prevention(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-OVER"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=50,
            reserved=40,  # available is 10
        ),
    )
    with pytest.raises(ValidationError) as exc:
        await service.adjust_stock(
            context=CoreContext.create(),
            inventory_id=item.id,
            adjustment_type=StockAdjustmentType.REMOVE,
            quantity=15,  # 15 > 10 available
        )
    assert "exceeds available" in str(exc.value)


@pytest.mark.asyncio
async def test_inactive_stock_adjustment_rejected(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-INACT"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.DRAFT,
            on_hand=50,
        ),
    )
    with pytest.raises(ValidationError):
        await service.adjust_stock(
            context=CoreContext.create(),
            inventory_id=item.id,
            adjustment_type=StockAdjustmentType.ADD,
            quantity=10,
        )


@pytest.mark.asyncio
async def test_correction_adjustment_rejected(service):
    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-CORR"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.ACTIVE,
            on_hand=50,
        ),
    )
    with pytest.raises(ValidationError):
        await service.adjust_stock(
            context=CoreContext.create(),
            inventory_id=item.id,
            adjustment_type=StockAdjustmentType.CORRECTION,
            quantity=10,
        )


@pytest.mark.asyncio
async def test_change_status(service, event_bus):
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("InventoryStatusChanged", handler)

    location = await service.create_location(
        context=CoreContext.create(),
        location=StockLocation(name="WH", code="WH-STAT"),
    )
    item = await service.create_inventory(
        context=CoreContext.create(),
        inventory=InventoryItem(
            variant_id=uuid4(),
            location_id=location.id,
            status=InventoryStatus.DRAFT,
            on_hand=50,
        ),
    )
    updated = await service.change_status(
        context=CoreContext.create(),
        inventory_id=item.id,
        target=InventoryStatus.ACTIVE,
    )
    assert updated.status == InventoryStatus.ACTIVE
    assert len(events) == 1
    assert events[0].entity_id == item.id
