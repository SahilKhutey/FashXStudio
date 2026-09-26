from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreferences,
)
from .enums import (
    AddressType,
    ConsentType,
)


class CustomerRepository(ABC):
    @abstractmethod
    async def get(
        self,
        customer_id: UUID,
    ) -> Customer | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_number(
        self,
        customer_number: str,
    ) -> Customer | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        customer: Customer,
    ) -> Customer:
        raise NotImplementedError


class CustomerAddressRepository(ABC):
    @abstractmethod
    async def get(
        self,
        address_id: UUID,
    ) -> CustomerAddress | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        address: CustomerAddress,
    ) -> CustomerAddress:
        raise NotImplementedError

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerAddress]:
        raise NotImplementedError

    @abstractmethod
    async def get_default(
        self,
        customer_id: UUID,
        address_type: AddressType,
    ) -> CustomerAddress | None:
        raise NotImplementedError


class CustomerPreferencesRepository(ABC):
    @abstractmethod
    async def get(
        self,
        customer_id: UUID,
    ) -> CustomerPreferences | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        preferences: CustomerPreferences,
    ) -> CustomerPreferences:
        raise NotImplementedError


class CustomerConsentRepository(ABC):
    @abstractmethod
    async def get(
        self,
        consent_id: UUID,
    ) -> CustomerConsent | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_type(
        self,
        customer_id: UUID,
        consent_type: ConsentType,
    ) -> CustomerConsent | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        consent: CustomerConsent,
    ) -> CustomerConsent:
        raise NotImplementedError

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerConsent]:
        raise NotImplementedError
