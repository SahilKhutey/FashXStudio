from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreferences,
    generate_customer_number,
)
from app.domain.customer.enums import (
    AddressType,
    ConsentType,
    CustomerStatus,
    CustomerType,
)


def test_customer_number_format():
    cust_num = generate_customer_number()
    assert cust_num.startswith("FX-CUST-")
    assert len(cust_num) == 18


def test_customer_with_customer_number_and_type():
    cust = Customer(
        customer_number="FX-CUST-CUSTOM1234",
        customer_type=CustomerType.BUSINESS,
        status=CustomerStatus.PENDING,
        first_name="Fashion",
        last_name="House",
        email="info@fashionhouse.com",
    )
    cust.validate()
    assert cust.customer_number == "FX-CUST-CUSTOM1234"
    assert cust.customer_type == CustomerType.BUSINESS
    assert cust.status == CustomerStatus.PENDING


def test_customer_preferences_validation():
    cid = uuid4()
    prefs = CustomerPreferences(
        customer_id=cid,
        preferred_currency="INR",
        preferred_region="IN-MH",
        language="en",
        categories=["dresses", "jackets"],
        brands=["Zara", "FashX"],
        styles=["minimalist"],
        sizes={"tops": "M", "shoes": "42"},
    )
    prefs.validate()
    assert prefs.customer_id == cid
    assert prefs.preferred_currency == "INR"
    assert prefs.categories == ["dresses", "jackets"]
    assert prefs.sizes["shoes"] == "42"


def test_customer_preferences_invalid_currency():
    prefs = CustomerPreferences(
        customer_id=uuid4(),
        preferred_currency="INVALID",
        language="en",
    )
    with pytest.raises(ValidationError, match="Currency must be a 3-character code"):
        prefs.validate()


def test_customer_preferences_missing_language():
    prefs = CustomerPreferences(
        customer_id=uuid4(),
        language="   ",
    )
    with pytest.raises(ValidationError, match="Language is required"):
        prefs.validate()


def test_customer_consent_validation():
    cid = uuid4()
    consent = CustomerConsent(
        customer_id=cid,
        consent_type=ConsentType.PERSONALIZATION,
        granted=True,
        version="1.0",
    )
    consent.validate()
    assert consent.customer_id == cid
    assert consent.consent_type == ConsentType.PERSONALIZATION
    assert consent.granted is True


def test_customer_consent_missing_customer():
    consent = CustomerConsent(
        customer_id=None,
        consent_type=ConsentType.MARKETING,
        version="1.0",
    )
    with pytest.raises(ValidationError, match="Consent requires customer_id"):
        consent.validate()


def test_customer_consent_missing_version():
    consent = CustomerConsent(
        customer_id=uuid4(),
        consent_type=ConsentType.PRIVACY,
        version="",
    )
    with pytest.raises(ValidationError, match="Consent version is required"):
        consent.validate()


def test_customer_address_types():
    cid = uuid4()
    addr = CustomerAddress(
        customer_id=cid,
        address_type=AddressType.BILLING,
        recipient_name="Finance Dept",
        address_line_1="100 Corporate Way",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        country="IN",
        is_default=True,
    )
    addr.validate()
    assert addr.address_type == AddressType.BILLING
    assert addr.is_default is True
