from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveryRequest:
    user_id: str
    surface: str = "for_you"
    category: str | None = None
    region: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class DiscoveryInteraction:
    user_id: str
    item_id: str
    action: str
