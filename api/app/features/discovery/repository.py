from collections.abc import Iterable

from .models import DiscoveryItem


class DiscoveryRepository:
    """Port implementation for controlled development data and catalog adapters."""

    def __init__(self, items: Iterable[DiscoveryItem] = ()) -> None:
        self._items = list(items)

    def add(self, item: DiscoveryItem) -> None:
        self._items.append(item)

    def all(self) -> tuple[DiscoveryItem, ...]:
        return tuple(self._items)

    def find(self, item_id: str) -> DiscoveryItem | None:
        return next((item for item in self._items if item.item_id == item_id), None)
