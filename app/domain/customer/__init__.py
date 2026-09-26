from .entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreference,
    CustomerPreferences,
    generate_customer_number,
)
from .enums import (
    AddressStatus,
    AddressType,
    ConsentType,
    CustomerStatus,
    CustomerType,
    PreferenceScope,
)
from .events import (
    AddressArchived,
    AddressCreated,
    CustomerAddressAdded,
    CustomerConsentChanged,
    CustomerCreated,
    CustomerPreferencesUpdated,
    CustomerStatusChanged,
    CustomerUpdated,
    DefaultAddressChanged,
    PreferenceChanged,
)
from .lifecycle import validate_customer_transition, validate_transition
from .repository import (
    CustomerAddressRepository,
    CustomerConsentRepository,
    CustomerPreferencesRepository,
    CustomerRepository,
)
from .service import CustomerService

__all__ = [
    "AddressArchived",
    "AddressCreated",
    "AddressStatus",
    "AddressType",
    "ConsentType",
    "Customer",
    "CustomerAddress",
    "CustomerAddressAdded",
    "CustomerAddressRepository",
    "CustomerConsent",
    "CustomerConsentChanged",
    "CustomerConsentRepository",
    "CustomerCreated",
    "CustomerPreference",
    "CustomerPreferences",
    "CustomerPreferencesRepository",
    "CustomerPreferencesUpdated",
    "CustomerRepository",
    "CustomerService",
    "CustomerStatus",
    "CustomerStatusChanged",
    "CustomerType",
    "CustomerUpdated",
    "DefaultAddressChanged",
    "PreferenceChanged",
    "PreferenceScope",
    "generate_customer_number",

    "validate_customer_transition",
    "validate_transition",
]
