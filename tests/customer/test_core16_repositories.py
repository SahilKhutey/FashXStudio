from uuid import uuid4

import pytest

from fashx.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreferences,
)
from fashx.domain.customer.enums import (
    AddressType,
    ConsentType,
)
from fashx.repositories.customer.memory import (
    InMemoryCustomerAddressRepository,
    InMemoryCustomerConsentRepository,
    InMemoryCustomerPreferencesRepository,
    InMemoryCustomerRepository,
)


@pytest.mark.asyncio
async def test_customer_number_repo_lookup():
    repo = InMemoryCustomerRepository()
    cust = Customer(
        customer_number="FX-CUST-1A2B3C4D5E",
        email="cust_num@test.com",
    )
    await repo.save(cust)

    found = await repo.get_by_number("FX-CUST-1A2B3C4D5E")
    assert found is not None
    assert found.id == cust.id

    not_found = await repo.get_by_number("FX-CUST-NONEXISTENT")
    assert not_found is None


@pytest.mark.asyncio
async def test_customer_preferences_repo():
    repo = InMemoryCustomerPreferencesRepository()
    cid = uuid4()
    prefs = CustomerPreferences(
        customer_id=cid,
        preferred_currency="EUR",
        language="de",
        categories=["sneakers"],
    )
    saved = await repo.save(prefs)
    assert saved.customer_id == cid

    fetched = await repo.get(cid)
    assert fetched is not None
    assert fetched.preferred_currency == "EUR"
    assert fetched.language == "de"
    assert fetched.categories == ["sneakers"]

    missing = await repo.get(uuid4())
    assert missing is None


@pytest.mark.asyncio
async def test_customer_consent_repo():
    repo = InMemoryCustomerConsentRepository()
    cid = uuid4()
    consent1 = CustomerConsent(
        customer_id=cid,
        consent_type=ConsentType.TERMS,
        granted=True,
        version="1.0",
    )
    consent2 = CustomerConsent(
        customer_id=cid,
        consent_type=ConsentType.MARKETING,
        granted=False,
        version="1.0",
    )

    await repo.save(consent1)
    await repo.save(consent2)

    by_id = await repo.get(consent1.id)
    assert by_id is not None
    assert by_id.granted is True

    by_type = await repo.get_by_type(cid, ConsentType.TERMS)
    assert by_type is not None
    assert by_type.id == consent1.id

    all_consents = await repo.list_by_customer(cid)
    assert len(all_consents) == 2


@pytest.mark.asyncio
async def test_customer_address_repo_get_default():
    repo = InMemoryCustomerAddressRepository()
    cid = uuid4()
    addr1 = CustomerAddress(
        customer_id=cid,
        address_type=AddressType.SHIPPING,
        recipient_name="Default Shipping",
        address_line_1="Line 1",
        city="Pune",
        state="MH",
        postal_code="411001",
        is_default=True,
    )
    addr2 = CustomerAddress(
        customer_id=cid,
        address_type=AddressType.BILLING,
        recipient_name="Default Billing",
        address_line_1="Line 2",
        city="Pune",
        state="MH",
        postal_code="411001",
        is_default=True,
    )
    await repo.save(addr1)
    await repo.save(addr2)

    def_ship = await repo.get_default(cid, AddressType.SHIPPING)
    assert def_ship is not None
    assert def_ship.id == addr1.id

    def_bill = await repo.get_default(cid, AddressType.BILLING)
    assert def_bill is not None
    assert def_bill.id == addr2.id
