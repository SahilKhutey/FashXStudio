from __future__ import annotations

from typing import Any


class CoreRegistry:
    """
    Runtime registry for Core services and infrastructure adapters.
    """

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        if not name.strip():
            raise ValueError("Registry name cannot be empty.")

        if name in self._items:
            raise ValueError(
                f"Core component already registered: {name}"
            )

        self._items[name] = instance

    def get(self, name: str) -> Any:
        try:
            return self._items[name]
        except KeyError as exc:
            raise KeyError(
                f"Core component not registered: {name}"
            ) from exc

    def contains(self, name: str) -> bool:
        return name in self._items

    def clear(self) -> None:
        self._items.clear()
