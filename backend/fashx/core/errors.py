from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    CORE_VALIDATION_ERROR = "CORE_VALIDATION_ERROR"
    ENTITY_NOT_FOUND = "entity_not_found"
    DUPLICATE_ENTITY = "duplicate_entity"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    CONSENT_REQUIRED = "consent_required"
    CONFLICT = "conflict"
    CORE_CONFLICT = "CORE_CONFLICT"
    NOT_FOUND = "CORE_NOT_FOUND"
    DEPENDENCY_ERROR = "CORE_DEPENDENCY_ERROR"
    PERMISSION_DENIED = "permission_denied"
    UNAUTHORIZED = "unauthorized"
    INTERNAL_ERROR = "internal_error"
    FORBIDDEN = "forbidden"
    PHOTO_INVALID = "photo_invalid"
    PHOTO_POOR_QUALITY = "photo_poor_quality"
    TRYON_FAILED = "tryon_failed"
    TRYON_CANCELLED = "tryon_cancelled"
    TRYON_TIMEOUT = "tryon_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    GARMENT_NOT_FOUND = "garment_not_found"
    OUT_OF_STOCK = "out_of_stock"
    MERCHANT_UNAVAILABLE = "merchant_unavailable"
    NAV_NOT_FOUND = "not_found"
    NAV_FORBIDDEN = "forbidden"
    NAV_DATA_FAILURE = "data_failure"
    NAV_FEATURE_DISABLED = "feature_disabled"


class _ConflictCode(str):
    def __eq__(self, other: Any) -> bool:
        return str(self) == other or other in ("conflict", "CORE_CONFLICT")

    def __hash__(self) -> int:
        return hash("CORE_CONFLICT")


class CoreError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.field = field

    def __str__(self) -> str:
        return self.message


class DomainError(CoreError):
    """Base exception for all domain and application errors."""

    def __init__(
        self,
        message: str,
        code: str = "domain_error",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, field=field)


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
    """Raised when domain-level or core-level validation rules are violated."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        resolved_code = code or ("validation_error" if field is not None and code is None else "CORE_VALIDATION_ERROR")
        super().__init__(message=message, code=resolved_code, field=field, details=details)


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


class ConflictError(DomainError):
    """Raised when an operation conflicts with current state."""

    def __init__(
        self,
        message: str = "Resource conflict",
        field: str | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        c = code or _ConflictCode("CORE_CONFLICT")
        super().__init__(message=message, code=c, field=field, details=details)
        self.status_code = 409


class NotFoundError(DomainError):
    """Raised when a generic resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="CORE_NOT_FOUND", field=field, details=details)
        self.status_code = 404


class DependencyError(CoreError):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="CORE_DEPENDENCY_ERROR",
            message=message,
            details=details,
        )


class AuthorizationError(DomainError):
    """Raised when user lacks permission for an operation."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message=message, code="permission_denied")
        self.status_code = 403
