"""Feature configuration and controlled runtime overrides."""

from collections.abc import Mapping
from dataclasses import dataclass

from .errors import FeatureConfigurationError


@dataclass(frozen=True)
class FeatureConfig:
    enabled: bool = True
    settings: Mapping[str, object] | None = None


class FeatureConfigStore:
    def __init__(self, configs: Mapping[str, FeatureConfig] | None = None) -> None:
        self._configs = dict(configs or {})

    def set(self, feature_id: str, config: FeatureConfig) -> None:
        if not feature_id.strip():
            raise FeatureConfigurationError("Feature ID cannot be empty")
        self._configs[feature_id] = config

    def get(self, feature_id: str) -> FeatureConfig:
        return self._configs.get(feature_id, FeatureConfig())

    def is_enabled(self, feature_id: str) -> bool:
        return self.get(feature_id).enabled
