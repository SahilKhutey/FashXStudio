from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CoreError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


class ValidationError(CoreError):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="CORE_VALIDATION_ERROR",
            message=message,
            details=details,
        )


class NotFoundError(CoreError):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="CORE_NOT_FOUND",
            message=message,
            details=details,
        )


class ConflictError(CoreError):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="CORE_CONFLICT",
            message=message,
            details=details,
        )


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
