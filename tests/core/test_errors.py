from app.core.errors import (
    ConflictError,
    DependencyError,
    NotFoundError,
    ValidationError,
)


def test_validation_error_code():
    error = ValidationError("invalid product")

    assert error.code == "CORE_VALIDATION_ERROR"
    assert str(error) == "invalid product"


def test_not_found_error_code():
    error = NotFoundError("product not found")

    assert error.code == "CORE_NOT_FOUND"


def test_conflict_error_code():
    error = ConflictError("duplicate product")

    assert error.code == "CORE_CONFLICT"


def test_dependency_error_code():
    error = DependencyError("service unavailable")

    assert error.code == "CORE_DEPENDENCY_ERROR"
