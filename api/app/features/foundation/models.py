"""Pure feature-layer models. No framework, database, or network imports."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FeatureStatus(StrEnum):
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"


class FeatureState(StrEnum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    ACTIVE = "active"
    EMPTY = "empty"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"


@dataclass(frozen=True)
class FeatureDefinition:
    feature_id: str
    name: str
    version: str
    description: str = ""
    dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.feature_id.strip():
            raise ValueError("feature_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.version.strip():
            raise ValueError("version cannot be empty")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError(f"Duplicate dependencies for feature {self.feature_id}")

    def has_dependency(self, feature_id: str) -> bool:
        return feature_id in self.dependencies
