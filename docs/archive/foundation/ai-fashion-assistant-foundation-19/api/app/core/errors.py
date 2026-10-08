from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    field: str | None = None
    details: dict[str, Any] | None = None


class NotFoundError(AppError):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(code="not_found", message=message, status_code=404, field=field)


class ConflictError(AppError):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(code="conflict", message=message, status_code=409, field=field)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(code="permission_denied", message=message, status_code=403)


class ConsentRequiredError(AppError):
    def __init__(self, data_type: str) -> None:
        super().__init__(
            code="consent_required",
            message=f"Consent required for {data_type}",
            status_code=403,
            field=data_type,
            details={"data_type": data_type},
        )
