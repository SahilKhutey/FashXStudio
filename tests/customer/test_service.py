from uuid import uuid4

import pytest

from fashx.core.context import CoreContext
from fashx.core.errors import ConflictError, NotFoundError, ValidationError
from fashx.core.event_bus import EventBus
from fashx.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerPreference,
)
from fashx.domain.customer.enums import (
    AddressStatus,
    CustomerStatus,
    PreferenceScope,
)
from fashx.domain.customer.events import (
    AddressArchived,
    AddressCreated,
    CustomerCreated,
    CustomerStatusChanged,
    CustomerUpdated,
    DefaultAddressChanged,
    PreferenceChanged,
)
from fashx.domain.customer.service import (
    CustomerService,
)
from fashx.repositories.customer.memory import (
    InMemoryCustomerAddressRepository,
    InMemoryCustomerPreferenceRepository,
    InMemoryCustomerRepository,
)


def build_service() -> tuple[CustomerService, list]:
    published_events = []
    bus = EventBus()

    async def handler(envelope):
        published_events.append(envelope.event)

    for event_name in [
        "CustomerCreated",
        "CustomerUpdated",
        "CustomerStatusChanged",
        "AddressCreated",
        "AddressArchived",
        "DefaultAddressChanged",
        "PreferenceChanged",
    ]:
        bus.subscribe(event_name, handler)

    service = CustomerService(
        customer_repository=InMemoryCustomerRepository(),
        address_repository=InMemoryCustomerAddressRepository(),
        preference_repository=InMemoryCustomerPreferenceRepository(),
        event_bus=bus,
    )
    return service, published_events


@pytest.mark.asyncio
async def test_create_customer():
    service, events = build_service()
    customer = Customer(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
    )
    result = await service.create_customer(
        context=CoreContext.create(),
        customer=customer,
    )
    assert result.id == customer.id
    assert len(events) == 1
    assert isinstance(events[0], CustomerCreated)
    assert events[0].entity_id == customer.id


@pytest.mark.asyncio
async def test_duplicate_email_rejected():
    service, _ = build_service()
    first = Customer(email="same@example.com")
    second = Customer(email="SAME@example.com")

    await service.create_customer(
        context=CoreContext.create(),
        customer=first,
    )

    with pytest.raises(ConflictError, match="Customer email already exists"):
        await service.create_customer(
            context=CoreContext.create(),
            customer=second,
        )


@pytest.mark.asyncio
async def test_duplicate_external_identity_rejected():
    service, _ = build_service()
    first = Customer(phone="+911234567890", external_identity_id="oauth-123")
    second = Customer(phone="+919876543210", external_identity_id="oauth-123")

    await service.create_customer(
        context=CoreContext.create(),
        customer=first,
    )

    with pytest.raises(ConflictError, match="External identity is already linked"):
        await service.create_customer(
            context=CoreContext.create(),
            customer=second,
        )


@pytest.mark.asyncio
async def test_get_customer_not_found():
    service, _ = build_service()
    with pytest.raises(NotFoundError, match="Customer was not found"):
        await service.get_customer(uuid4())


@pytest.mark.asyncio
async def test_update_customer():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="edit@example.com", first_name="Old"),
    )

    updated = await service.update_customer(
        context=CoreContext.create(),
        customer_id=customer.id,
        first_name="New",
        last_name="Name",
        phone="+919999999999",
    )
    assert updated.first_name == "New"
    assert updated.last_name == "Name"
    assert updated.phone == "+919999999999"
    assert updated.version == 2
    assert any(isinstance(e, CustomerUpdated) for e in events)


@pytest.mark.asyncio
async def test_change_status():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="status@example.com"),
    )

    suspended = await service.change_status(
        context=CoreContext.create(),
        customer_id=customer.id,
        target=CustomerStatus.SUSPENDED,
    )
    assert suspended.status == CustomerStatus.SUSPENDED
    assert any(isinstance(e, CustomerStatusChanged) for e in events)

    deactivated = await service.change_status(
        context=CoreContext.create(),
        customer_id=customer.id,
        target=CustomerStatus.DEACTIVATED,
    )
    assert deactivated.status == CustomerStatus.DEACTIVATED

    # Terminal state check
    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        await service.change_status(
            context=CoreContext.create(),
            customer_id=customer.id,
            target=CustomerStatus.ACTIVE,
        )


@pytest.mark.asyncio
async def test_first_address_becomes_default():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="address@example.com"),
    )

    address = CustomerAddress(
        customer_id=customer.id,
        recipient_name="Test",
        address_line_1="Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )

    result = await service.add_address(
        context=CoreContext.create(),
        address=address,
    )
    assert result.is_default is True
    assert any(isinstance(e, AddressCreated) for e in events)


@pytest.mark.asyncio
async def test_subsequent_address_explicit_default():
    service, _ = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="multiaddr@example.com"),
    )

    addr1 = CustomerAddress(
        customer_id=customer.id,
        recipient_name="Home",
        address_line_1="Street 1",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    res1 = await service.add_address(context=CoreContext.create(), address=addr1)
    assert res1.is_default is True

    addr2 = CustomerAddress(
        customer_id=customer.id,
        recipient_name="Work",
        address_line_1="Street 2",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492002",
        is_default=True,
    )
    res2 = await service.add_address(context=CoreContext.create(), address=addr2)
    assert res2.is_default is True

    # addr1 should now not be default
    addresses = await service.list_addresses(customer.id)
    addr_map = {a.id: a for a in addresses}
    assert addr_map[res1.id].is_default is False
    assert addr_map[res2.id].is_default is True


@pytest.mark.asyncio
async def test_customer_address_belongs_to_customer():
    service, _ = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="owner@example.com"),
    )

    address = CustomerAddress(
        customer_id=customer.id,
        recipient_name="Test",
        address_line_1="Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )

    await service.add_address(
        context=CoreContext.create(),
        address=address,
    )
    assert address.customer_id == customer.id


@pytest.mark.asyncio
async def test_archive_address():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="archive@example.com"),
    )

    address = CustomerAddress(
        customer_id=customer.id,
        recipient_name="Test",
        address_line_1="Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    created = await service.add_address(context=CoreContext.create(), address=address)
    assert created.is_default is True

    archived = await service.archive_address(
        context=CoreContext.create(),
        address_id=created.id,
    )
    assert archived.status == AddressStatus.ARCHIVED
    assert archived.is_default is False
    assert any(isinstance(e, AddressArchived) for e in events)


@pytest.mark.asyncio
async def test_archive_address_not_found():
    service, _ = build_service()
    with pytest.raises(NotFoundError, match="Address was not found"):
        await service.archive_address(
            context=CoreContext.create(),
            address_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_set_default_address():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="setdefault@example.com"),
    )

    addr1 = await service.add_address(
        context=CoreContext.create(),
        address=CustomerAddress(
            customer_id=customer.id,
            recipient_name="Addr1",
            address_line_1="L1",
            city="Raipur",
            state="CG",
            postal_code="492001",
        ),
    )
    addr2 = await service.add_address(
        context=CoreContext.create(),
        address=CustomerAddress(
            customer_id=customer.id,
            recipient_name="Addr2",
            address_line_1="L2",
            city="Raipur",
            state="CG",
            postal_code="492002",
        ),
    )

    assert addr1.is_default is True
    assert addr2.is_default is False

    # Switch default to addr2
    await service.set_default_address(
        context=CoreContext.create(),
        customer_id=customer.id,
        address_id=addr2.id,
    )

    addrs = await service.list_addresses(customer.id)
    addr_map = {a.id: a for a in addrs}
    assert addr_map[addr1.id].is_default is False
    assert addr_map[addr2.id].is_default is True
    assert any(isinstance(e, DefaultAddressChanged) for e in events)


@pytest.mark.asyncio
async def test_set_default_address_errors():
    service, _ = build_service()
    c1 = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="c1@example.com"),
    )
    c2 = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="c2@example.com"),
    )

    addr1 = await service.add_address(
        context=CoreContext.create(),
        address=CustomerAddress(
            customer_id=c1.id,
            recipient_name="Addr1",
            address_line_1="L1",
            city="Raipur",
            state="CG",
            postal_code="492001",
        ),
    )

    # Address does not belong to c2
    with pytest.raises(ConflictError, match="does not belong to customer"):
        await service.set_default_address(
            context=CoreContext.create(),
            customer_id=c2.id,
            address_id=addr1.id,
        )

    # Archived address cannot be default
    await service.archive_address(context=CoreContext.create(), address_id=addr1.id)
    with pytest.raises(ConflictError, match="Archived address cannot be default"):
        await service.set_default_address(
            context=CoreContext.create(),
            customer_id=c1.id,
            address_id=addr1.id,
        )


@pytest.mark.asyncio
async def test_preference_management():
    service, events = build_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="pref@example.com"),
    )

    pref = CustomerPreference(
        customer_id=customer.id,
        scope=PreferenceScope.COMMERCE,
        key="currency",
        value="INR",
    )
    saved = await service.set_preference(
        context=CoreContext.create(),
        preference=pref,
    )
    assert saved.key == "currency"
    assert any(isinstance(e, PreferenceChanged) for e in events)

    prefs = await service.list_preferences(customer.id)
    assert len(prefs) == 1
    assert prefs[0].key == "currency"
    assert prefs[0].value == "INR"
