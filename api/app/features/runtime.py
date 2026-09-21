"""Runtime feature initialization and state transitions.

The runtime owns availability resolution only. It does not own a feature's
data or business operations, which remain in the consuming feature module.
"""

from schemas.features.v1 import (
    FeatureAvailability,
    FeatureEvent,
    FeatureEventType,
    FeatureLifecycle,
    FeatureRuntimeSnapshot,
    FeatureRuntimeState,
)

from .application import FeatureAvailabilityService


class FeatureRuntime:
    def __init__(
        self,
        availability_service: FeatureAvailabilityService,
        feature_flags: dict[str, bool] | None = None,
    ) -> None:
        self.availability_service = availability_service
        self.feature_flags = feature_flags or {}
        self._states: dict[str, FeatureRuntimeState] = {}

    def initialize(self, feature_id: str) -> FeatureRuntimeSnapshot | None:
        availability = self.availability_service.availability(feature_id)
        if availability is None:
            return None
        enabled = self.feature_flags.get(feature_id, True)
        disabled_dependencies = self._disabled_dependencies(availability.feature.id)
        enabled = enabled and not disabled_dependencies
        state = (
            FeatureRuntimeState.READY
            if enabled and availability.available
            else FeatureRuntimeState.DISABLED
        )
        self._states[feature_id] = state
        return self.snapshot(availability, enabled, disabled_dependencies)

    def _disabled_dependencies(self, feature_id: str) -> list[str]:
        feature = self.availability_service.registry.get(feature_id)
        if feature is None:
            return []
        disabled: list[str] = []
        for dependency_id in feature.depends_on:
            if not self.feature_flags.get(dependency_id, True):
                disabled.append(dependency_id)
            disabled.extend(self._disabled_dependencies(dependency_id))
        return list(dict.fromkeys(disabled))

    def transition(self, feature_id: str, state: FeatureRuntimeState) -> FeatureRuntimeSnapshot | None:
        availability = self.availability_service.availability(feature_id)
        if availability is None:
            return None
        enabled = self.feature_flags.get(feature_id, True)
        if not enabled or not availability.available:
            state = FeatureRuntimeState.DISABLED
        self._states[feature_id] = state
        return self.snapshot(availability, enabled, [])

    def snapshot(
        self,
        availability: FeatureAvailability,
        enabled_by_configuration: bool,
        disabled_dependencies: list[str] | None = None,
    ) -> FeatureRuntimeSnapshot:
        reasons = list(availability.unavailable_reasons)
        if not enabled_by_configuration:
            reasons.append("Feature is disabled by runtime configuration.")
        if disabled_dependencies:
            reasons.extend(
                f"Dependency '{dependency_id}' is disabled by runtime configuration."
                for dependency_id in disabled_dependencies
            )
        return FeatureRuntimeSnapshot(
            feature_id=availability.feature.id,
            lifecycle=(
                FeatureLifecycle.READY
                if self._states.get(availability.feature.id) == FeatureRuntimeState.READY
                else FeatureLifecycle.DISABLED
            ),
            state=self._states.get(availability.feature.id, FeatureRuntimeState.REGISTERED),
            enabled_by_configuration=enabled_by_configuration,
            available=enabled_by_configuration and availability.available,
            unavailable_reasons=reasons,
        )


class InMemoryFeatureEventPublisher:
    """Testable event boundary until Core event infrastructure is connected."""

    def __init__(self) -> None:
        self.events: list[FeatureEvent] = []

    def publish(self, event: FeatureEvent) -> None:
        self.events.append(event)


def lifecycle_event_type(state: FeatureRuntimeState) -> FeatureEventType:
    if state == FeatureRuntimeState.READY:
        return FeatureEventType.LOADED
    if state == FeatureRuntimeState.FAILED:
        return FeatureEventType.FAILED
    return FeatureEventType.UPDATED
