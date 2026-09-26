from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShipmentCreationResult:
    success: bool
    tracking_number: str | None = None
    provider_shipment_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class CarrierProvider(ABC):
    @abstractmethod
    async def create_shipment(
        self,
        *,
        shipment_id: str,
        shipping_method: str,
        address: dict[str, str],
    ) -> ShipmentCreationResult:
        raise NotImplementedError

    @abstractmethod
    async def cancel_shipment(
        self,
        *,
        provider_shipment_id: str,
    ) -> ShipmentCreationResult:
        raise NotImplementedError


class TestCarrierProvider(CarrierProvider):
    async def create_shipment(
        self,
        *,
        shipment_id: str,
        shipping_method: str,
        address: dict[str, str],
    ) -> ShipmentCreationResult:
        return ShipmentCreationResult(
            success=True,
            tracking_number=f"TEST-{shipment_id[:8]}",
            provider_shipment_id=f"SHIP-{shipment_id[:8]}",
        )

    async def cancel_shipment(
        self,
        *,
        provider_shipment_id: str,
    ) -> ShipmentCreationResult:
        return ShipmentCreationResult(
            success=True,
            provider_shipment_id=provider_shipment_id,
        )
