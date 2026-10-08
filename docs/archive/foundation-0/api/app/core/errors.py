from typing import Any


class DomainError(Exception):
    """Base exception for all domain and application errors."""

    def __init__(self, message: str, code: str = "domain_error", field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


class EntityNotFoundError(DomainError):
    """Raised when an entity cannot be found by its identifier or query criteria."""

    def __init__(
        self,
        entity_type: str,
        entity_id: Any = None,
        message: str | None = None,
    ) -> None:
        msg = message or f"{entity_type} with identifier '{entity_id}' was not found."
        super().__init__(message=msg, code="entity_not_found")
        self.entity_type = entity_type
        self.entity_id = str(entity_id) if entity_id is not None else None


class DuplicateEntityError(DomainError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(
        self,
        entity_type: str,
        key: str,
        value: Any,
        message: str | None = None,
    ) -> None:
        msg = message or f"{entity_type} with {key}='{value}' already exists."
        super().__init__(message=msg, code="duplicate_entity", field=key)
        self.entity_type = entity_type
        self.key = key
        self.value = str(value)


class ValidationError(DomainError):
    """Raised when domain-level validation rules are violated."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message=message, code="validation_error", field=field)


class IdempotencyConflictError(DomainError):
    """Raised when an idempotent request encounters an in-flight conflict or payload mismatch."""

    def __init__(self, message: str, code: str = "idempotency_conflict") -> None:
        super().__init__(message=message, code=code)


class ConsentRequiredError(DomainError):
    """Raised when an operation requires user consent that has not been granted."""

    def __init__(
        self,
        data_type: str,
        message: str | None = None,
    ) -> None:
        msg = message or f"Consent for '{data_type}' has not been granted by user."
        super().__init__(message=msg, code="consent_required", field="consent")
        self.data_type = data_type
