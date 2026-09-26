from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class CancellationRequested(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CancellationCompleted(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReturnRequested(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReturnAccepted(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReturnRejected(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RefundRequested(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RefundCompleted(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RefundFailed(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReplacementRequested(DomainEvent):
    entity_id: UUID | None = None
