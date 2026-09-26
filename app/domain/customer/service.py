from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
)
from app.core.event_bus import EventBus

from .entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreference,
    CustomerPreferences,
    generate_customer_number,
)
from .enums import AddressStatus, CustomerStatus
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
from .lifecycle import validate_transition
from .repository import (
    CustomerAddressRepository,
    CustomerConsentRepository,
    CustomerPreferencesRepository,
    CustomerRepository,
)


class CustomerService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        address_repository: CustomerAddressRepository,
        preferences_repository: CustomerPreferencesRepository | None = None,
        consent_repository: CustomerConsentRepository | None = None,
        event_bus: EventBus | None = None,
        preference_repository: Any = None,
    ):
        self.customer_repository = customer_repository
        self.address_repository = address_repository
        self.preferences_repository = preferences_repository or preference_repository
        self.preference_repository = preference_repository or preferences_repository
        self.consent_repository = consent_repository
        self.event_bus = event_bus

    async def _publish(self, event: Any) -> None:
        if self.event_bus is not None:
            await self.event_bus.publish(event)

    async def create_customer(
        self,
        *,
        context: CoreContext,
        customer: Customer,
    ) -> Customer:
        if not customer.customer_number:
            customer.customer_number = generate_customer_number()

        customer.validate()

        if hasattr(self.customer_repository, "get_by_number"):
            existing = await self.customer_repository.get_by_number(
                customer.customer_number
            )
            if existing:
                raise ConflictError("Customer number already exists.")

        if customer.email and hasattr(self.customer_repository, "get_by_email"):
            existing_email = await self.customer_repository.get_by_email(customer.email)
            if existing_email:
                raise ConflictError("Customer email already exists.")

        if (
            customer.external_identity_id
            and hasattr(self.customer_repository, "get_by_external_identity")
        ):
            existing_ext = await self.customer_repository.get_by_external_identity(
                customer.external_identity_id
            )
            if existing_ext:
                raise ConflictError("External identity is already linked.")

        await self.customer_repository.save(customer)

        await self._publish(
            CustomerCreated(
                entity_id=customer.id,
                correlation_id=context.correlation_id,
            )
        )

        return customer

    async def get_customer(
        self,
        customer_id: UUID,
    ) -> Customer:
        customer = await self.customer_repository.get(customer_id)

        if customer is None:
            raise NotFoundError("Customer was not found.")

        return customer

    async def update_customer(
        self,
        *,
        context: CoreContext,
        customer: Customer | None = None,
        customer_id: UUID | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
    ) -> Customer:
        if customer is not None:
            target = await self.get_customer(customer.id)
            target.first_name = customer.first_name
            target.last_name = customer.last_name
            target.display_name = customer.display_name
            target.phone = customer.phone
            target.email = customer.email
            target.validate()
            target.touch()
            await self.customer_repository.save(target)
            await self._publish(
                CustomerUpdated(
                    entity_id=target.id,
                    correlation_id=context.correlation_id,
                )
            )
            return target

        if customer_id is not None:
            target = await self.get_customer(customer_id)
            if first_name is not None:
                target.first_name = first_name
            if last_name is not None:
                target.last_name = last_name
            if phone is not None:
                target.phone = phone
            target.validate()
            target.touch()
            await self.customer_repository.save(target)
            await self._publish(
                CustomerUpdated(
                    entity_id=target.id,
                    correlation_id=context.correlation_id,
                )
            )
            return target

        raise NotFoundError("Customer was not found.")

    async def change_status(
        self,
        *,
        context: CoreContext,
        customer_id: UUID,
        target: CustomerStatus,
    ) -> Customer:
        customer = await self.get_customer(customer_id)

        validate_transition(
            customer.status,
            target,
        )

        customer.status = target
        customer.touch()

        await self.customer_repository.save(customer)

        await self._publish(
            CustomerStatusChanged(
                entity_id=customer.id,
                correlation_id=context.correlation_id,
            )
        )

        return customer

    async def add_address(
        self,
        *,
        context: CoreContext,
        address: CustomerAddress,
    ) -> CustomerAddress:
        if address.customer_id is not None:
            await self.get_customer(address.customer_id)

        address.validate()

        if address.customer_id is not None:
            existing = await self.address_repository.list_by_customer(
                address.customer_id
            )

            if len(existing) == 0:
                address.is_default = True
            elif address.is_default:
                for item in existing:
                    if item.is_default:
                        item.is_default = False
                        item.touch()
                        await self.address_repository.save(item)

        await self.address_repository.save(address)

        await self._publish(
            CustomerAddressAdded(
                entity_id=address.id,
                correlation_id=context.correlation_id,
            )
        )
        await self._publish(
            AddressCreated(
                entity_id=address.id,
                correlation_id=context.correlation_id,
            )
        )

        return address

    async def archive_address(
        self,
        *,
        context: CoreContext,
        address_id: UUID,
    ) -> CustomerAddress:
        address = await self.address_repository.get(address_id)
        if address is None:
            raise NotFoundError("Address was not found.")

        address.status = AddressStatus.ARCHIVED
        address.is_default = False
        address.touch()
        await self.address_repository.save(address)

        await self._publish(
            AddressArchived(
                entity_id=address.id,
                correlation_id=context.correlation_id,
            )
        )
        return address

    async def set_default_address(
        self,
        *,
        context: CoreContext,
        customer_id: UUID,
        address_id: UUID,
    ) -> CustomerAddress:
        address = await self.address_repository.get(address_id)
        if address is None:
            raise NotFoundError("Address was not found.")

        if address.customer_id != customer_id:
            raise ConflictError("Address does not belong to customer.")

        if address.status == AddressStatus.ARCHIVED:
            raise ConflictError("Archived address cannot be default.")

        addresses = await self.address_repository.list_by_customer(customer_id)
        for item in addresses:
            if item.id != address_id and item.is_default:
                item.is_default = False
                item.touch()
                await self.address_repository.save(item)

        address.is_default = True
        address.touch()
        await self.address_repository.save(address)

        await self._publish(
            DefaultAddressChanged(
                entity_id=address.id,
                correlation_id=context.correlation_id,
            )
        )
        return address

    async def list_addresses(
        self,
        customer_id: UUID,
    ) -> list[CustomerAddress]:
        await self.get_customer(customer_id)
        return await self.address_repository.list_by_customer(customer_id)

    async def save_preferences(
        self,
        *,
        context: CoreContext,
        preferences: CustomerPreferences,
    ) -> CustomerPreferences:
        if preferences.customer_id is not None:
            await self.get_customer(preferences.customer_id)

        preferences.validate()

        if self.preferences_repository is not None:
            await self.preferences_repository.save(preferences)

        await self._publish(
            CustomerPreferencesUpdated(
                entity_id=preferences.customer_id,
                correlation_id=context.correlation_id,
            )
        )

        return preferences

    async def set_preference(
        self,
        *,
        context: CoreContext,
        preference: CustomerPreference,
    ) -> CustomerPreference:
        if preference.customer_id is not None:
            await self.get_customer(preference.customer_id)

        preference.validate()

        if self.preference_repository is not None and hasattr(
            self.preference_repository, "save"
        ):
            await self.preference_repository.save(preference)

        await self._publish(
            PreferenceChanged(
                entity_id=preference.customer_id,
                correlation_id=context.correlation_id,
            )
        )

        return preference

    async def list_preferences(
        self,
        customer_id: UUID,
    ) -> list[CustomerPreference]:
        if self.preference_repository is not None and hasattr(
            self.preference_repository, "list_by_customer"
        ):
            return await self.preference_repository.list_by_customer(customer_id)
        return []

    async def save_consent(
        self,
        *,
        context: CoreContext,
        consent: CustomerConsent,
    ) -> CustomerConsent:
        if consent.customer_id is not None:
            await self.get_customer(consent.customer_id)

        consent.validate()

        if self.consent_repository is not None:
            await self.consent_repository.save(consent)

        await self._publish(
            CustomerConsentChanged(
                entity_id=consent.customer_id,
                correlation_id=context.correlation_id,
            )
        )

        return consent
