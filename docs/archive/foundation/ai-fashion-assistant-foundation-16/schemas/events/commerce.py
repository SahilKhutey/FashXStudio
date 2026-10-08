from datetime import datetime
from pydantic import Field
from uuid import UUID

from schemas.events.base import DomainEvent


class BuyClicked(DomainEvent):
    event_type: str = "buy_clicked"
    object_type: str = "merchant_offer"
    payload: dict[str, object] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        garment_id: UUID,
        offer_id: UUID,
        tracking_id: str,
        affiliate_network: str,
        trace_id: UUID | None,
        occurred_at: datetime,
        event_id: UUID,
    ) -> "BuyClicked":
        return cls(
            event_id=event_id,
            user_id=user_id,
            object_id=offer_id,
            trace_id=trace_id,
            occurred_at=occurred_at,
            payload={
                "garment_id": str(garment_id),
                "offer_id": str(offer_id),
                "tracking_id": tracking_id,
                "affiliate_network": affiliate_network,
            },
        )
