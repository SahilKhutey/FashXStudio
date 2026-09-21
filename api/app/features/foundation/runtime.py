"""Per-feature state machine. Runtime state is never global."""

from .errors import FeatureDisabledError, FeatureLifecycleError
from .models import FeatureDefinition, FeatureState


class FeatureRuntime:
    def __init__(self, definition: FeatureDefinition, enabled: bool | None = None) -> None:
        self.definition = definition
        self.state = FeatureState.UNINITIALIZED if definition.enabled and enabled is not False else FeatureState.DISABLED

    def initialize(self) -> None:
        if self.state == FeatureState.DISABLED:
            raise FeatureDisabledError(f"Feature is disabled: {self.definition.feature_id}")
        if self.state not in {FeatureState.UNINITIALIZED, FeatureState.RECOVERING}:
            raise FeatureLifecycleError(f"Cannot initialize from state {self.state.value}")
        self.state = FeatureState.INITIALIZING
        self.state = FeatureState.READY

    def start(self) -> None:
        if self.state == FeatureState.DISABLED:
            raise FeatureDisabledError(f"Feature is disabled: {self.definition.feature_id}")
        if self.state != FeatureState.READY:
            raise FeatureLifecycleError(f"Cannot start from state {self.state.value}")
        self.state = FeatureState.ACTIVE

    def complete(self) -> None:
        if self.state != FeatureState.ACTIVE:
            raise FeatureLifecycleError(f"Cannot complete from state {self.state.value}")
        self.state = FeatureState.READY

    def fail(self) -> None:
        self.state = FeatureState.FAILED

    def recover(self) -> None:
        if self.state != FeatureState.FAILED:
            raise FeatureLifecycleError(f"Cannot recover from state {self.state.value}")
        self.state = FeatureState.RECOVERING
        self.state = FeatureState.READY
