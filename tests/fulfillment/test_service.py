from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.event_bus import EventBus
from fashx.domain.fulfillment.carrier import (
    CarrierProvider,
    ShipmentCreationResult,
    TestCarrierProvider,
)
from fashx.domain.fulfillment.entities import (
    AddressSnapshot,
    Fulfillment,
    FulfillmentLine,
    Shipment,
)
from fashx.domain.fulfillment.enums import (
    DeliveryStatus,
    FulfillmentStatus,
    ShipmentStatus,
)
from fashx.domain.fulfillment.service import (
    FulfillmentService,
)
from fashx.repositories.fulfillment.memory import (
    InMemoryFulfillmentLineRepository,
    InMemoryFulfillmentRepository,
    InMemoryShipmentRepository,
)


def sample_address() -> AddressSnapshot:
    return AddressSnapshot(
        recipient_name="Customer Name",
        address_line_1="123 Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def service(event_bus: EventBus) -> FulfillmentService:
    return FulfillmentService(
        fulfillment_repository=InMemoryFulfillmentRepository(),
        line_repository=InMemoryFulfillmentLineRepository(),
        shipment_repository=InMemoryShipmentRepository(),
        event_bus=event_bus,
        carrier=TestCarrierProvider(),
    )


@pytest.mark.asyncio
async def test_create_fulfillment(
    service: FulfillmentService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("FulfillmentCreated", handler)

    order_id = uuid4()
    fulfillment = Fulfillment(
        order_id=order_id,
        address=sample_address(),
    )
    order_line_id = uuid4()
    product_id = uuid4()
    lines = [
        FulfillmentLine(
            order_line_id=order_line_id,
            product_id=product_id,
            quantity=2,
        )
    ]

    result = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=fulfillment,
        lines=lines,
    )

    assert result.status == FulfillmentStatus.CREATED
    assert len(events) == 1
    assert events[0].entity_id == result.id

    saved_lines = await service.line_repository.list_by_fulfillment(result.id)
    assert len(saved_lines) == 1
    assert saved_lines[0].order_line_id == order_line_id


@pytest.mark.asyncio
async def test_create_fulfillment_empty_lines(
    service: FulfillmentService,
) -> None:
    fulfillment = Fulfillment(
        order_id=uuid4(),
        address=sample_address(),
    )
    with pytest.raises(
        ConflictError, match="requires at least one line"
    ):
        await service.create_fulfillment(
            context=CoreContext.create(),
            fulfillment=fulfillment,
            lines=[],
        )


@pytest.mark.asyncio
async def test_get_fulfillment(service: FulfillmentService) -> None:
    fulfillment = Fulfillment(
        order_id=uuid4(),
        address=sample_address(),
    )
    await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=fulfillment,
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
            )
        ],
    )

    fetched = await service.get_fulfillment(fulfillment.id)
    assert fetched.id == fulfillment.id

    with pytest.raises(NotFoundError):
        await service.get_fulfillment(uuid4())


@pytest.mark.asyncio
async def test_change_fulfillment_status(
    service: FulfillmentService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("FulfillmentStatusChanged", handler)

    fulfillment = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=uuid4(),
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
            )
        ],
    )

    updated = await service.change_fulfillment_status(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        target=FulfillmentStatus.PROCESSING,
    )
    assert updated.status == FulfillmentStatus.PROCESSING
    assert len(events) == 1

    # Invalid transition PROCESSING -> CREATED
    with pytest.raises(ValidationError):
        await service.change_fulfillment_status(
            context=CoreContext.create(),
            fulfillment_id=fulfillment.id,
            target=FulfillmentStatus.CREATED,
        )


@pytest.mark.asyncio
async def test_create_shipment_flow(
    service: FulfillmentService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("ShipmentCreated", handler)

    fulfillment = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=uuid4(),
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
            )
        ],
    )

    # Attempting shipment while CREATED raises ConflictError
    with pytest.raises(ConflictError, match="current fulfillment state"):
        await service.create_shipment(
            context=CoreContext.create(),
            fulfillment_id=fulfillment.id,
            shipment=Shipment(carrier="test-carrier"),
        )

    # Transition to PROCESSING
    await service.change_fulfillment_status(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        target=FulfillmentStatus.PROCESSING,
    )

    shipment = await service.create_shipment(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        shipment=Shipment(carrier="test-carrier"),
    )

    assert shipment.status == ShipmentStatus.LABEL_CREATED
    assert shipment.tracking_number is not None
    assert shipment.metadata.get("provider_shipment_id") is not None
    assert len(events) == 1
    assert events[0].entity_id == shipment.id


@pytest.mark.asyncio
async def test_create_shipment_carrier_failure(
    event_bus: EventBus,
) -> None:
    class FailingCarrier(CarrierProvider):
        async def create_shipment(
            self, *, shipment_id, shipping_method, address
        ):
            return ShipmentCreationResult(
                success=False,
                error_code="SERVICE_UNAVAILABLE",
                error_message="Courier outage",
            )

        async def cancel_shipment(self, *, provider_shipment_id):
            raise NotImplementedError

    service = FulfillmentService(
        fulfillment_repository=InMemoryFulfillmentRepository(),
        line_repository=InMemoryFulfillmentLineRepository(),
        shipment_repository=InMemoryShipmentRepository(),
        event_bus=event_bus,
        carrier=FailingCarrier(),
    )

    fulfillment = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=uuid4(),
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
            )
        ],
    )
    await service.change_fulfillment_status(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        target=FulfillmentStatus.PROCESSING,
    )

    with pytest.raises(ConflictError, match="Carrier failed to create shipment"):
        await service.create_shipment(
            context=CoreContext.create(),
            fulfillment_id=fulfillment.id,
            shipment=Shipment(carrier="failing-carrier"),
        )


@pytest.mark.asyncio
async def test_change_shipment_status_and_delivery(
    service: FulfillmentService, event_bus: EventBus
) -> None:
    events_status = []
    events_delivered = []

    async def status_handler(envelope):
        events_status.append(envelope.event)

    async def delivered_handler(envelope):
        events_delivered.append(envelope.event)

    event_bus.subscribe("ShipmentStatusChanged", status_handler)
    event_bus.subscribe("ShipmentDelivered", delivered_handler)

    fulfillment = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=uuid4(),
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
            )
        ],
    )
    await service.change_fulfillment_status(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        target=FulfillmentStatus.PROCESSING,
    )
    shipment = await service.create_shipment(
        context=CoreContext.create(),
        fulfillment_id=fulfillment.id,
        shipment=Shipment(carrier="test-carrier"),
    )

    # LABEL_CREATED -> PICKED_UP
    shipment = await service.change_shipment_status(
        context=CoreContext.create(),
        shipment_id=shipment.id,
        target=ShipmentStatus.PICKED_UP,
    )
    assert shipment.status == ShipmentStatus.PICKED_UP

    # PICKED_UP -> IN_TRANSIT
    shipment = await service.change_shipment_status(
        context=CoreContext.create(),
        shipment_id=shipment.id,
        target=ShipmentStatus.IN_TRANSIT,
    )
    assert shipment.status == ShipmentStatus.IN_TRANSIT

    # IN_TRANSIT -> OUT_FOR_DELIVERY
    shipment = await service.change_shipment_status(
        context=CoreContext.create(),
        shipment_id=shipment.id,
        target=ShipmentStatus.OUT_FOR_DELIVERY,
    )
    assert shipment.status == ShipmentStatus.OUT_FOR_DELIVERY

    # OUT_FOR_DELIVERY -> DELIVERED
    shipment = await service.change_shipment_status(
        context=CoreContext.create(),
        shipment_id=shipment.id,
        target=ShipmentStatus.DELIVERED,
    )
    assert shipment.status == ShipmentStatus.DELIVERED
    assert shipment.delivery_status == DeliveryStatus.DELIVERED
    assert len(events_delivered) == 1
    assert events_delivered[0].entity_id == shipment.id


@pytest.mark.asyncio
async def test_partial_fulfillment_foundation(
    service: FulfillmentService,
) -> None:
    order_id = uuid4()

    # Fulfillment 1: Item A
    ful1 = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=order_id,
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
                quantity=1,
            )
        ],
    )

    # Fulfillment 2: Item B & C
    ful2 = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=Fulfillment(
            order_id=order_id,
            address=sample_address(),
        ),
        lines=[
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
                quantity=1,
            ),
            FulfillmentLine(
                order_line_id=uuid4(),
                product_id=uuid4(),
                quantity=2,
            ),
        ],
    )

    fulfillments = await service.fulfillment_repository.list_by_order(order_id)
    assert len(fulfillments) == 2
    assert {f.id for f in fulfillments} == {ful1.id, ful2.id}
