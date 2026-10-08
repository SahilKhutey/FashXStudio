from uuid import uuid4

import pytest

from fashx.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerPreference,
)
from fashx.domain.customer.enums import PreferenceScope
from fashx.repositories.customer.memory import (
    InMemoryCustomerAddressRepository,
    InMemoryCustomerPreferenceRepository,
    InMemoryCustomerRepository,
)


@pytest.mark.asyncio
async def test_customer_repository_crud():
    repo = InMemoryCustomerRepository()
    customer = Customer(
        email="User@Domain.Com",
        external_identity_id="ext-12345",
        first_name="Jane",
        last_name="Doe",
    )
    saved = await repo.save(customer)
    assert saved.id == customer.id

    fetched = await repo.get(customer.id)
    assert fetched is not None
    assert fetched.id == customer.id
    assert fetched.first_name == "Jane"

    by_ext = await repo.get_by_external_identity("ext-12345")
    assert by_ext is not None
    assert by_ext.id == customer.id

    missing_ext = await repo.get_by_external_identity("non-existent")
    assert missing_ext is None

    # Case-insensitive email lookup
    by_email_lower = await repo.get_by_email("user@domain.com")
    assert by_email_lower is not None
    assert by_email_lower.id == customer.id

    by_email_padded = await repo.get_by_email("  USER@DOMAIN.COM  ")
    assert by_email_padded is not None
    assert by_email_padded.id == customer.id

    missing_email = await repo.get_by_email("other@domain.com")
    assert missing_email is None

    missing = await repo.get(uuid4())
    assert missing is None


@pytest.mark.asyncio
async def test_customer_address_repository():
    repo = InMemoryCustomerAddressRepository()
    customer_id = uuid4()
    address1 = CustomerAddress(
        customer_id=customer_id,
        recipient_name="Jane",
        address_line_1="Line 1",
        city="Mumbai",
        state="MH",
        postal_code="400001",
    )
    address2 = CustomerAddress(
        customer_id=customer_id,
        recipient_name="Jane",
        address_line_1="Line 2",
        city="Mumbai",
        state="MH",
        postal_code="400002",
    )
    other_address = CustomerAddress(
        customer_id=uuid4(),
        recipient_name="Other",
        address_line_1="Other St",
        city="Delhi",
        state="DL",
        postal_code="110001",
    )

    await repo.save(address1)
    await repo.save(address2)
    await repo.save(other_address)

    fetched = await repo.get(address1.id)
    assert fetched is not None
    assert fetched.id == address1.id

    missing = await repo.get(uuid4())
    assert missing is None

    customer_addresses = await repo.list_by_customer(customer_id)
    assert len(customer_addresses) == 2
    address_ids = {a.id for a in customer_addresses}
    assert address1.id in address_ids
    assert address2.id in address_ids


@pytest.mark.asyncio
async def test_customer_preference_repository():
    repo = InMemoryCustomerPreferenceRepository()
    customer_id = uuid4()
    pref1 = CustomerPreference(
        customer_id=customer_id,
        scope=PreferenceScope.COMMERCE,
        key="currency",
        value="INR",
    )
    pref2 = CustomerPreference(
        customer_id=customer_id,
        scope=PreferenceScope.UI,
        key="theme",
        value="dark",
    )
    other_pref = CustomerPreference(
        customer_id=uuid4(),
        scope=PreferenceScope.UI,
        key="theme",
        value="light",
    )

    await repo.save(pref1)
    await repo.save(pref2)
    await repo.save(other_pref)

    prefs = await repo.list_by_customer(customer_id)
    assert len(prefs) == 2
    keys = {p.key for p in prefs}
    assert "currency" in keys
    assert "theme" in keys
