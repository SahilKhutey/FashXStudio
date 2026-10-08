"""Deterministic, cycle-safe feature dependency resolution."""

from .errors import FeatureCircularDependencyError, FeatureDependencyError
from .registry import FeatureRegistry


class DependencyResolver:
    def __init__(self, registry: FeatureRegistry) -> None:
        self.registry = registry

    def resolve(self, feature_id: str) -> tuple[str, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[str] = []

        def visit(current: str) -> None:
            if current in visiting:
                raise FeatureCircularDependencyError(f"Circular dependency involving {current}")
            if current in visited:
                return
            if not self.registry.contains(current):
                raise FeatureDependencyError(f"Unknown feature dependency: {current}")
            visiting.add(current)
            for dependency in self.registry.get(current).dependencies:
                visit(dependency)
            visiting.remove(current)
            visited.add(current)
            ordered.append(current)

        visit(feature_id)
        return tuple(ordered)
