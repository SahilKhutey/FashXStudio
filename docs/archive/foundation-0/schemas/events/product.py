from schemas.events.base import DomainEvent


class ProductRejected(DomainEvent):
    event_type: str = "product_rejected"
