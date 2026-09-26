from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.payments.provider import (
    TestPaymentProvider,
)


@pytest.mark.asyncio
async def test_provider_authorization() -> None:
    provider = TestPaymentProvider()

    result = await provider.authorize(
        amount=Decimal("500"),
        currency="INR",
        payment_method="upi",
        metadata={},
    )

    assert result.success is True
    assert result.provider_payment_id == "test-payment"
    assert result.provider_transaction_id == "test-auth"


@pytest.mark.asyncio
async def test_provider_capture() -> None:
    provider = TestPaymentProvider()

    result = await provider.capture(
        provider_payment_id="test-payment",
        amount=Decimal("500"),
        currency="INR",
    )

    assert result.success is True
    assert result.provider_payment_id == "test-payment"
    assert result.provider_transaction_id == "test-capture"


@pytest.mark.asyncio
async def test_provider_cancel() -> None:
    provider = TestPaymentProvider()

    result = await provider.cancel(
        provider_payment_id="test-payment",
    )

    assert result.success is True
    assert result.provider_payment_id == "test-payment"
