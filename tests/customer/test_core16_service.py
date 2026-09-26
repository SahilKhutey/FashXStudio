from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import ConflictError, NotFoundError
from app.core.event_bus import EventBus
from app.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreferences,
)
from app.domain.customer.enums import (
    AddressType,
    ConsentType,
)
from app.domain.customer.events import (
    CustomerAddressAdded,
    CustomerConsentChanged,
    CustomerPreferencesUpdated,
)
from app.domain.customer.service import CustomerService
from app.repositories.customer.memory import (
    InMemoryCustomerAddressRepository,
    InMemoryCustomerConsentRepository,
    InMemoryCustomerPreferencesRepository,
    InMemoryCustomerRepository,
)


def build_core16_service() -> tuple[CustomerService, list]:
    published_events = []
    bus = EventBus()

    async def handler(envelope):
        published_events.append(envelope.event)

    for event_name in [
        "CustomerCreated",
        "CustomerUpdated",
        "CustomerStatusChanged",
        "CustomerAddressAdded",
        "CustomerPreferencesUpdated",
        "CustomerConsentChanged",
    ]:
        bus.subscribe(event_name, handler)

    service = CustomerService(
        customer_repository=InMemoryCustomerRepository(),
        address_repository=InMemoryCustomerAddressRepository(),
        preferences_repository=InMemoryCustomerPreferencesRepository(),
        consent_repository=InMemoryCustomerConsentRepository(),
        event_bus=bus,
    )
    return service, published_events


@pytest.mark.asyncio
async def test_save_preferences():
    service, events = build_core16_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="pref_test@example.com", first_name="Maya"),
    )

    prefs = CustomerPreferences(
        customer_id=customer.id,
        preferred_currency="USD",
        categories=["accessories", "shoes"],
        brands=["Acne Studios"],
    )
    saved = await service.save_preferences(
        context=CoreContext.create(),
        preferences=prefs,
    )
    assert saved.customer_id == customer.id
    assert saved.preferred_currency == "USD"
    assert any(isinstance(e, CustomerPreferencesUpdated) for e in events)


@pytest.mark.asyncio
async def test_save_preferences_customer_not_found():
    service, _ = build_core16_service()
    prefs = CustomerPreferences(
        customer_id=uuid4(),
        preferred_currency="USD",
    )
    with pytest.raises(NotFoundError, match="Customer was not found"):
        await service.save_preferences(
            context=CoreContext.create(),
            preferences=prefs,
        )


@pytest.mark.asyncio
async def test_save_consent():
    service, events = build_core16_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="consent_test@example.com", first_name="Aarav"),
    )

    consent = CustomerConsent(
        customer_id=customer.id,
        consent_type=ConsentType.MARKETING,
        granted=True,
        version="2.0",
    )
    saved = await service.save_consent(
        context=CoreContext.create(),
        consent=consent,
    )
    assert saved.customer_id == customer.id
    assert saved.consent_type == ConsentType.MARKETING
    assert any(isinstance(e, CustomerConsentChanged) for e in events)


@pytest.mark.asyncio
async def test_save_consent_customer_not_found():
    service, _ = build_core16_service()
    consent = CustomerConsent(
        customer_id=uuid4(),
        consent_type=ConsentType.PRIVACY,
        granted=True,
    )
    with pytest.raises(NotFoundError, match="Customer was not found"):
        await service.save_consent(
            context=CoreContext.create(),
            consent=consent,
        )


@pytest.mark.asyncio
async def test_customer_number_conflict():
    service, _ = build_core16_service()
    cust1 = Customer(
        customer_number="FX-CUST-DUPLICATE1",
        email="cust1@example.com",
    )
    cust2 = Customer(
        customer_number="FX-CUST-DUPLICATE1",
        email="cust2@example.com",
    )

    await service.create_customer(context=CoreContext.create(), customer=cust1)
    with pytest.raises(ConflictError, match="Customer number already exists"):
        await service.create_customer(context=CoreContext.create(), customer=cust2)


@pytest.mark.asyncio
async def test_add_address_events():
    service, events = build_core16_service()
    customer = await service.create_customer(
        context=CoreContext.create(),
        customer=Customer(email="addr_event@example.com"),
    )

    addr = CustomerAddress(
        customer_id=customer.id,
        address_type=AddressType.SHIPPING,
        recipient_name="Recipient",
        address_line_1="Line 1",
        city="Mumbai",
        state="MH",
        postal_code="400001",
    )
    await service.add_address(context=CoreContext.create(), address=addr)
    assert any(isinstance(e, CustomerAddressAdded) for e in events)
