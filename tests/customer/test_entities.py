from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerPreference,
)
from fashx.domain.customer.enums import (
    AddressStatus,
    AddressType,
    CustomerStatus,
    PreferenceScope,
)


def test_customer_requires_contact():
    customer = Customer()
    with pytest.raises(ValidationError, match="Customer requires email or phone"):
        customer.validate()


def test_customer_email():
    customer = Customer(email="customer@example.com")
    customer.validate()
    assert customer.status == CustomerStatus.ACTIVE
    assert customer.version == 1


def test_customer_phone():
    customer = Customer(phone="+919876543210")
    customer.validate()
    assert customer.phone == "+919876543210"


def test_customer_invalid_email():
    customer = Customer(email="not-an-email")
    with pytest.raises(ValidationError, match="Customer email is invalid"):
        customer.validate()


def test_customer_invalid_version():
    customer = Customer(email="user@test.com", version=0)
    with pytest.raises(ValidationError, match="version must be positive"):
        customer.validate()


def test_customer_touch():
    customer = Customer(email="user@test.com")
    orig_time = customer.updated_at
    customer.touch()
    assert customer.version == 2
    assert customer.updated_at >= orig_time


def test_address_requires_customer():
    address = CustomerAddress(
        recipient_name="Test",
        address_line_1="Main Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    with pytest.raises(ValidationError, match="Address requires customer ID"):
        address.validate()


@pytest.mark.parametrize(
    "field_name",
    [
        "recipient_name",
        "address_line_1",
        "city",
        "state",
        "postal_code",
        "country",
    ],
)
def test_address_missing_required_fields(field_name: str):
    valid_data = {
        "customer_id": uuid4(),
        "recipient_name": "Test Name",
        "address_line_1": "123 Main St",
        "city": "Raipur",
        "state": "Chhattisgarh",
        "postal_code": "492001",
        "country": "IN",
    }
    valid_data[field_name] = "  "
    address = CustomerAddress(**valid_data)
    with pytest.raises(ValidationError, match=f"{field_name} is required"):
        address.validate()


def test_valid_address():
    address = CustomerAddress(
        customer_id=uuid4(),
        recipient_name="Test",
        address_line_1="Main Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    address.validate()
    assert address.address_type == AddressType.HOME
    assert address.status == AddressStatus.ACTIVE
    assert address.is_default is False


def test_address_touch():
    address = CustomerAddress(
        customer_id=uuid4(),
        recipient_name="Test",
        address_line_1="Main Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    orig_time = address.updated_at
    address.touch()
    assert address.version == 2
    assert address.updated_at >= orig_time


def test_preference_validation():
    pref = CustomerPreference(key="theme", value="dark")
    with pytest.raises(ValidationError, match="Preference requires customer ID"):
        pref.validate()

    pref2 = CustomerPreference(customer_id=uuid4(), key="   ", value="dark")
    with pytest.raises(ValidationError, match="Preference key is required"):
        pref2.validate()

    pref3 = CustomerPreference(
        customer_id=uuid4(),
        scope=PreferenceScope.UI,
        key="theme",
        value="dark",
    )
    pref3.validate()
    pref3.touch()
    assert pref3.scope == PreferenceScope.UI
