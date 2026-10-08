import pytest

from fashx.features.foundation import (
    DependencyResolver,
    FeatureDefinition,
    FeatureManager,
    FeatureRegistry,
    FeatureRuntime,
    FeatureState,
)
from fashx.features.foundation.errors import (
    FeatureAlreadyRegisteredError,
    FeatureCircularDependencyError,
    FeatureDependencyError,
    FeatureLifecycleError,
)


def feature(feature_id: str, dependencies: tuple[str, ...] = ()) -> FeatureDefinition:
    return FeatureDefinition(feature_id, feature_id, "1.0.0", dependencies=dependencies)


def test_definition_rejects_empty_ids_and_duplicate_dependencies() -> None:
    with pytest.raises(ValueError):
        feature("")
    with pytest.raises(ValueError):
        feature("FX-X", ("FX-A", "FX-A"))


def test_registry_rejects_duplicates() -> None:
    registry = FeatureRegistry()
    registry.register(feature("FX-A"))
    with pytest.raises(FeatureAlreadyRegisteredError):
        registry.register(feature("FX-A"))


def test_dependency_resolution_is_ordered_and_cycle_safe() -> None:
    registry = FeatureRegistry()
    registry.register_many((feature("FX-A"), feature("FX-B", ("FX-A",)), feature("FX-C", ("FX-B",))))
    assert DependencyResolver(registry).resolve("FX-C") == ("FX-A", "FX-B", "FX-C")
    registry = FeatureRegistry()
    registry.register_many((feature("FX-A", ("FX-B",)), feature("FX-B", ("FX-A",))))
    with pytest.raises(FeatureCircularDependencyError):
        DependencyResolver(registry).resolve("FX-A")
    registry = FeatureRegistry()
    registry.register(feature("FX-A", ("FX-MISSING",)))
    with pytest.raises(FeatureDependencyError):
        DependencyResolver(registry).resolve("FX-A")


def test_runtime_enforces_lifecycle() -> None:
    runtime = FeatureRuntime(feature("FX-A"))
    with pytest.raises(FeatureLifecycleError):
        runtime.start()
    runtime.initialize()
    runtime.start()
    assert runtime.state == FeatureState.ACTIVE
    runtime.complete()
    assert runtime.state == FeatureState.READY


def test_manager_initializes_dependencies_and_publishes_events() -> None:
    manager = FeatureManager()
    received: list[str] = []
    manager.events.subscribe("feature.ready", lambda event: received.append(event.feature_id))
    manager.register(feature("FX-A"))
    manager.register(feature("FX-B", ("FX-A",)))
    manager.initialize("FX-B")
    assert manager.state("FX-A") == FeatureState.READY
    assert manager.state("FX-B") == FeatureState.READY
    assert received == ["FX-A", "FX-B"]
