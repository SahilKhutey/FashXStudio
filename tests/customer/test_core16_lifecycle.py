import pytest

from app.core.errors import ValidationError
from fashx.domain.customer.enums import CustomerStatus
from fashx.domain.customer.lifecycle import validate_transition


def test_core16_pending_transitions():
    # Valid
    validate_transition(CustomerStatus.PENDING, CustomerStatus.ACTIVE)
    validate_transition(CustomerStatus.PENDING, CustomerStatus.CLOSED)

    # Invalid
    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_transition(CustomerStatus.PENDING, CustomerStatus.SUSPENDED)


def test_core16_active_transitions():
    # Valid
    validate_transition(CustomerStatus.ACTIVE, CustomerStatus.SUSPENDED)
    validate_transition(CustomerStatus.ACTIVE, CustomerStatus.CLOSED)


def test_core16_suspended_transitions():
    # Valid
    validate_transition(CustomerStatus.SUSPENDED, CustomerStatus.ACTIVE)
    validate_transition(CustomerStatus.SUSPENDED, CustomerStatus.CLOSED)


def test_core16_closed_is_terminal():
    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_transition(CustomerStatus.CLOSED, CustomerStatus.ACTIVE)

    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_transition(CustomerStatus.CLOSED, CustomerStatus.PENDING)

    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_transition(CustomerStatus.CLOSED, CustomerStatus.SUSPENDED)
