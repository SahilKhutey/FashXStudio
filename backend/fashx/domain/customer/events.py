from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class CustomerCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CustomerUpdated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CustomerStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CustomerAddressAdded(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CustomerPreferencesUpdated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CustomerConsentChanged(DomainEvent):
    entity_id: UUID | None = None


# Legacy events for backward compatibility
@dataclass(frozen=True, slots=True)
class AddressCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AddressArchived(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class DefaultAddressChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PreferenceChanged(DomainEvent):
    entity_id: UUID | None = None

