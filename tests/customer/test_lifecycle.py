import pytest

from app.core.errors import ValidationError
from fashx.domain.customer.enums import (
    CustomerStatus,
)
from fashx.domain.customer.lifecycle import (
    validate_customer_transition,
)


def test_active_to_suspended():
    validate_customer_transition(
        CustomerStatus.ACTIVE,
        CustomerStatus.SUSPENDED,
    )


def test_active_to_deactivated():
    validate_customer_transition(
        CustomerStatus.ACTIVE,
        CustomerStatus.DEACTIVATED,
    )


def test_suspended_to_active():
    validate_customer_transition(
        CustomerStatus.SUSPENDED,
        CustomerStatus.ACTIVE,
    )


def test_suspended_to_deactivated():
    validate_customer_transition(
        CustomerStatus.SUSPENDED,
        CustomerStatus.DEACTIVATED,
    )


def test_deactivated_is_terminal():
    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_customer_transition(
            CustomerStatus.DEACTIVATED,
            CustomerStatus.ACTIVE,
        )

    with pytest.raises(ValidationError, match="Invalid customer status transition"):
        validate_customer_transition(
            CustomerStatus.DEACTIVATED,
            CustomerStatus.SUSPENDED,
        )
