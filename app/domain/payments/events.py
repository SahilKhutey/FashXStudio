from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class PaymentCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PaymentAuthorized(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PaymentCaptured(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PaymentFailed(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PaymentCancelled(DomainEvent):
    entity_id: UUID | None = None
