from __future__ import annotations

import pytest

from app.domain.fulfillment.carrier import (
    TestCarrierProvider,
)


@pytest.mark.asyncio
async def test_test_carrier_create_and_cancel() -> None:
    carrier = TestCarrierProvider()

    result = await carrier.create_shipment(
        shipment_id="ship-12345678",
        shipping_method="standard",
        address={
            "recipient_name": "Customer",
            "city": "Raipur",
        },
    )

    assert result.success is True
    assert result.tracking_number == "TEST-ship-123"
    assert result.provider_shipment_id == "SHIP-ship-123"

    cancel_res = await carrier.cancel_shipment(
        provider_shipment_id="SHIP-ship-123"
    )
    assert cancel_res.success is True
    assert cancel_res.provider_shipment_id == "SHIP-ship-123"
