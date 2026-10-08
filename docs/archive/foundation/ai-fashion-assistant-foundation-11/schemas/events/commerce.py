from schemas.events.base import DomainEvent


class BuyClicked(DomainEvent):
    event_type: str = "buy_clicked"
