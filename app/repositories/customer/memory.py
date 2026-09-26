from uuid import UUID

from app.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreference,
    CustomerPreferences,
)
from app.domain.customer.enums import (
    AddressType,
    ConsentType,
)
from app.domain.customer.repository import (
    CustomerAddressRepository,
    CustomerConsentRepository,
    CustomerPreferencesRepository,
    CustomerRepository,
)


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Customer] = {}
        self._numbers: dict[str, UUID] = {}

    async def get(self, customer_id: UUID) -> Customer | None:
        return self._items.get(customer_id)

    async def get_by_number(self, customer_number: str) -> Customer | None:
        customer_id = self._numbers.get(customer_number)
        if customer_id is None:
            return None
        return self._items.get(customer_id)

    async def save(self, customer: Customer) -> Customer:
        self._items[customer.id] = customer
        if customer.customer_number:
            self._numbers[customer.customer_number] = customer.id
        return customer

    async def get_by_external_identity(
        self,
        external_identity_id: str,
    ) -> Customer | None:
        for customer in self._items.values():
            if customer.external_identity_id == external_identity_id:
                return customer
        return None

    async def get_by_email(self, email: str) -> Customer | None:
        normalized = email.strip().lower()
        for customer in self._items.values():
            if customer.email and customer.email.strip().lower() == normalized:
                return customer
        return None


class InMemoryCustomerAddressRepository(CustomerAddressRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CustomerAddress] = {}

    async def get(self, address_id: UUID) -> CustomerAddress | None:
        return self._items.get(address_id)

    async def save(self, address: CustomerAddress) -> CustomerAddress:
        self._items[address.id] = address
        return address

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerAddress]:
        return [
            item
            for item in self._items.values()
            if item.customer_id == customer_id
        ]

    async def get_default(
        self,
        customer_id: UUID,
        address_type: AddressType,
    ) -> CustomerAddress | None:
        for item in self._items.values():
            if (
                item.customer_id == customer_id
                and item.address_type == address_type
                and item.is_default
            ):
                return item
        return None



class InMemoryCustomerPreferencesRepository(CustomerPreferencesRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CustomerPreferences] = {}

    async def get(self, customer_id: UUID) -> CustomerPreferences | None:
        return self._items.get(customer_id)

    async def save(
        self,
        preferences: CustomerPreferences,
    ) -> CustomerPreferences:
        if preferences.customer_id is not None:
            self._items[preferences.customer_id] = preferences
        return preferences


class InMemoryCustomerConsentRepository(CustomerConsentRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CustomerConsent] = {}

    async def save(
        self,
        consent: CustomerConsent,
    ) -> CustomerConsent:
        self._items[consent.id] = consent
        return consent

    async def get(self, consent_id: UUID) -> CustomerConsent | None:
        return self._items.get(consent_id)

    async def get_by_type(
        self,
        customer_id: UUID,
        consent_type: ConsentType,
    ) -> CustomerConsent | None:
        for item in self._items.values():
            if item.customer_id == customer_id and item.consent_type == consent_type:
                return item
        return None

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerConsent]:
        return [
            item
            for item in self._items.values()
            if item.customer_id == customer_id
        ]



# Backward compatibility
class InMemoryCustomerPreferenceRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, CustomerPreference] = {}

    async def save(
        self,
        preference: CustomerPreference,
    ) -> CustomerPreference:
        self._items[preference.id] = preference
        return preference

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerPreference]:
        return [
            preference
            for preference in self._items.values()
            if preference.customer_id == customer_id
        ]
