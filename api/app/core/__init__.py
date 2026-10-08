from .errors import (
    AuthorizationError,
    ConflictError,
    ConsentRequiredError,
    CoreError,
    DependencyError,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    IdempotencyConflictError,
    NotFoundError,
    ValidationError,
)

try:
    from .context import CoreContext
except ImportError:
    CoreContext = None

try:
    from .event_bus import EventBus
    from .events import DomainEvent, EntityCreated, EntityDeleted, EntityUpdated
except ImportError:
    EventBus = DomainEvent = EntityCreated = EntityDeleted = EntityUpdated = None

try:
    from .ids import new_id, parse_id
except ImportError:
    new_id = parse_id = None

try:
    from .registry import CoreRegistry
except ImportError:
    CoreRegistry = None

try:
    from .result import Failure, Success
except ImportError:
    Failure = Success = None

try:
    from .version import CORE_API_VERSION, CORE_VERSION
except ImportError:
    CORE_API_VERSION = CORE_VERSION = None

try:
    from .idempotency import (
        ClaimResult,
        IdempotencyManager,
        IdempotencyRecord,
        IdempotencyStatus,
        default_idempotency_manager,
    )
except ImportError:
    ClaimResult = IdempotencyManager = IdempotencyRecord = IdempotencyStatus = default_idempotency_manager = None

try:
    from .repository import BaseRepository
except ImportError:
    BaseRepository = None

try:
    from .unit_of_work import SqlAlchemyUnitOfWork, UnitOfWork
except ImportError:
    SqlAlchemyUnitOfWork = UnitOfWork = None

__all__ = [
    "AuthorizationError",
    "BaseRepository",
    "ClaimResult",
    "ConflictError",
    "ConsentRequiredError",
    "CoreContext",
    "CoreError",
    "CORE_API_VERSION",
    "CORE_VERSION",
    "DependencyError",
    "DomainError",
    "DomainEvent",
    "DuplicateEntityError",
    "EntityCreated",
    "EntityDeleted",
    "EntityNotFoundError",
    "EntityUpdated",
    "EventBus",
    "Failure",
    "CoreRegistry",
    "IdempotencyManager",
    "IdempotencyRecord",
    "IdempotencyStatus",
    "IdempotencyConflictError",
    "NotFoundError",
    "SqlAlchemyUnitOfWork",
    "Success",
    "UnitOfWork",
    "ValidationError",
    "default_idempotency_manager",
    "new_id",
    "parse_id",
]
