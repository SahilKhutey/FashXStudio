from __future__ import annotations

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.payments.enums import PaymentStatus
from fashx.domain.payments.lifecycle import validate_payment_transition


def test_created_to_authorized() -> None:
    validate_payment_transition(
        PaymentStatus.CREATED,
        PaymentStatus.AUTHORIZED,
    )


def test_created_to_requires_action() -> None:
    validate_payment_transition(
        PaymentStatus.CREATED,
        PaymentStatus.REQUIRES_ACTION,
    )


def test_requires_action_to_authorized() -> None:
    validate_payment_transition(
        PaymentStatus.REQUIRES_ACTION,
        PaymentStatus.AUTHORIZED,
    )


def test_authorized_to_captured() -> None:
    validate_payment_transition(
        PaymentStatus.AUTHORIZED,
        PaymentStatus.CAPTURED,
    )


def test_cancellation_paths() -> None:
    validate_payment_transition(
        PaymentStatus.CREATED,
        PaymentStatus.CANCELLED,
    )
    validate_payment_transition(
        PaymentStatus.REQUIRES_ACTION,
        PaymentStatus.CANCELLED,
    )
    validate_payment_transition(
        PaymentStatus.AUTHORIZED,
        PaymentStatus.CANCELLED,
    )


def test_captured_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid payment status transition"
    ):
        validate_payment_transition(
            PaymentStatus.CAPTURED,
            PaymentStatus.CANCELLED,
        )


def test_failed_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid payment status transition"
    ):
        validate_payment_transition(
            PaymentStatus.FAILED,
            PaymentStatus.AUTHORIZED,
        )


def test_cancelled_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid payment status transition"
    ):
        validate_payment_transition(
            PaymentStatus.CANCELLED,
            PaymentStatus.CREATED,
        )
