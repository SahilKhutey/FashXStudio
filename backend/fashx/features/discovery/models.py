from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .enums import DiscoveryItemType


@dataclass(frozen=True)
class DiscoveryItem:
    item_id: str
    item_type: DiscoveryItemType
    title: str
    description: str = ""
    image_url: str | None = None
    category: str | None = None
    tags: tuple[str, ...] = ()
    region: str | None = None
    trend_score: float = 0.0
    relevance_score: float = 0.0
    popularity_score: float = 0.0
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DiscoveryResult:
    items: tuple[DiscoveryItem, ...]
    total: int
    surface: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
