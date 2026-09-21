"""Feature definition registry with duplicate protection."""

from collections.abc import Iterable

from .errors import FeatureAlreadyRegisteredError, FeatureNotFoundError
from .models import FeatureDefinition


class FeatureRegistry:
    def __init__(self) -> None:
        self._features: dict[str, FeatureDefinition] = {}

    def register(self, feature: FeatureDefinition) -> None:
        if feature.feature_id in self._features:
            raise FeatureAlreadyRegisteredError(f"Feature already registered: {feature.feature_id}")
        self._features[feature.feature_id] = feature

    def get(self, feature_id: str) -> FeatureDefinition:
        try:
            return self._features[feature_id]
        except KeyError as exc:
            raise FeatureNotFoundError(f"Feature not found: {feature_id}") from exc

    def contains(self, feature_id: str) -> bool:
        return feature_id in self._features

    def all(self) -> tuple[FeatureDefinition, ...]:
        return tuple(self._features.values())

    def register_many(self, features: Iterable[FeatureDefinition]) -> None:
        for feature in features:
            self.register(feature)
