"""Coordinates registry, flags, dependency order, runtime state, and events."""

from .config import FeatureConfigStore
from .dependency import DependencyResolver
from .errors import FeatureDisabledError
from .events import FeatureEvent, FeatureEventBus
from .models import FeatureDefinition, FeatureState
from .registry import FeatureRegistry
from .runtime import FeatureRuntime


class FeatureManager:
    def __init__(
        self,
        registry: FeatureRegistry | None = None,
        config: FeatureConfigStore | None = None,
        events: FeatureEventBus | None = None,
    ) -> None:
        self.registry = registry or FeatureRegistry()
        self.config = config or FeatureConfigStore()
        self.events = events or FeatureEventBus()
        self._runtimes: dict[str, FeatureRuntime] = {}

    def register(self, feature: FeatureDefinition) -> None:
        self.registry.register(feature)
        self.events.publish(FeatureEvent(name="feature.registered", feature_id=feature.feature_id))

    def runtime(self, feature_id: str) -> FeatureRuntime:
        if feature_id not in self._runtimes:
            definition = self.registry.get(feature_id)
            self._runtimes[feature_id] = FeatureRuntime(
                definition, enabled=self.config.is_enabled(feature_id)
            )
        return self._runtimes[feature_id]

    def initialize(self, feature_id: str) -> None:
        if not self.config.is_enabled(feature_id):
            raise FeatureDisabledError(f"Feature disabled by configuration: {feature_id}")
        for dependency_id in DependencyResolver(self.registry).resolve(feature_id):
            runtime = self.runtime(dependency_id)
            if runtime.state == FeatureState.UNINITIALIZED:
                runtime.initialize()
                self.events.publish(FeatureEvent(name="feature.ready", feature_id=dependency_id))

    def start(self, feature_id: str) -> None:
        self.runtime(feature_id).start()
        self.events.publish(FeatureEvent(name="feature.started", feature_id=feature_id))

    def complete(self, feature_id: str) -> None:
        self.runtime(feature_id).complete()
        self.events.publish(FeatureEvent(name="feature.completed", feature_id=feature_id))

    def state(self, feature_id: str) -> FeatureState:
        return self.runtime(feature_id).state
