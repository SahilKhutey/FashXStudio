"""Registry and configuration management for catalog source adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fashx.catalog.acquisition.contract import CatalogSourceAdapter


@dataclass
class SourceConfig:
    """Operational configuration for a catalog acquisition adapter."""

    source_slug: str
    name: str
    kind: str = "api"  # api | feed_url | file_drop | manual
    image_policy: str = "mirror"  # mirror | hotlink
    refresh_hours: int = 24
    max_rps: float = 2.0
    timeout_seconds: float = 15.0
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_cooldown_seconds: float = 60.0
    extra_settings: dict[str, Any] = field(default_factory=dict)


class AdapterRegistry:
    """Thread-safe catalog adapter registry."""

    def __init__(self) -> None:
        self._adapters: dict[str, CatalogSourceAdapter] = {}
        self._configs: dict[str, SourceConfig] = {}

    def register(
        self,
        adapter: CatalogSourceAdapter,
        config: SourceConfig | None = None,
    ) -> None:
        slug = adapter.source_slug
        self._adapters[slug] = adapter
        if config is not None:
            self._configs[slug] = config
        elif slug not in self._configs:
            self._configs[slug] = SourceConfig(
                source_slug=slug,
                name=slug.replace("-", " ").title(),
            )

    def get(self, source_slug: str) -> CatalogSourceAdapter:
        if source_slug not in self._adapters:
            raise KeyError(f"No catalog adapter registered for source '{source_slug}'")
        return self._adapters[source_slug]

    def get_config(self, source_slug: str) -> SourceConfig | None:
        return self._configs.get(source_slug)

    def list_sources(self) -> list[str]:
        return sorted(self._adapters.keys())

    def unregister(self, source_slug: str) -> None:
        self._adapters.pop(source_slug, None)
        self._configs.pop(source_slug, None)

    def clear(self) -> None:
        self._adapters.clear()
        self._configs.clear()


_default_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Return the global default adapter registry."""
    return _default_registry
