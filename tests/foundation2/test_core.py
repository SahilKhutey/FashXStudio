import pytest

from api.app.core.errors import ConflictError
from api.app.core.idempotency import request_fingerprint
from fashx.domain.validation import validate_budget, validate_confidence
from fashx.domain.versioning import next_version


def test_fingerprint_is_deterministic() -> None:
    assert request_fingerprint("u", "g", 1) == request_fingerprint("u", "g", 1)
    assert request_fingerprint("u", "g", 1) != request_fingerprint("u", "g", 2)


def test_budget_validation() -> None:
    validate_budget(100, 200)
    validate_budget(None, 200)
    with pytest.raises(ValueError):
        validate_budget(300, 200)


def test_confidence_validation() -> None:
    assert validate_confidence(0.0) == 0.0
    assert validate_confidence(1.0) == 1.0
    with pytest.raises(ValueError):
        validate_confidence(1.1)


def test_version_increment() -> None:
    assert next_version(1) == 2
    with pytest.raises(ValueError):
        next_version(0)


def test_conflict_error_shape() -> None:
    error = ConflictError("duplicate")
    assert error.code == "conflict"
    assert error.status_code == 409
