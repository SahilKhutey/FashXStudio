from datetime import UTC, datetime

from fashx.features.application import FeatureAvailabilityService
from fashx.features.registry import FeatureRegistry
from fashx.features.runtime import (
    FeatureRuntime,
    InMemoryFeatureEventPublisher,
    lifecycle_event_type,
)
from schemas.features.v1 import (
    FeatureEvent,
    FeatureEventType,
    FeatureRuntimeState,
)


def test_feature_registry_exposes_unique_versioned_feature_ids() -> None:
    features = FeatureRegistry().list()

    assert features
    assert len({feature.id for feature in features}) == len(features)
    assert features[0].id == "FX-F00"
    assert features[0].version == "1.0.0"
    assert features[0].status == "enabled"


def test_feature_availability_requires_enabled_dependencies() -> None:
    service = FeatureAvailabilityService()

    foundation = service.availability("FX-F01")
    discovery = service.availability("FX-F03")

    assert foundation is not None and foundation.available
    assert discovery is not None and discovery.available


def test_unknown_feature_is_not_available() -> None:
    assert FeatureAvailabilityService().availability("FX-F99") is None


def test_runtime_respects_feature_flags_and_dependency_availability() -> None:
    runtime = FeatureRuntime(FeatureAvailabilityService(), {"FX-F01": False})

    disabled = runtime.initialize("FX-F01")
    blocked = runtime.initialize("FX-F03")

    assert disabled is not None
    assert disabled.state == FeatureRuntimeState.DISABLED
    assert disabled.available is False
    assert "Feature is disabled by runtime configuration." in disabled.unavailable_reasons
    assert blocked is not None
    assert blocked.state == FeatureRuntimeState.DISABLED


def test_runtime_event_boundary_preserves_the_versioned_event_contract() -> None:
    publisher = InMemoryFeatureEventPublisher()
    event = FeatureEvent(
        feature_id="FX-F01",
        event_type=FeatureEventType.INITIALIZED,
        occurred_at=datetime.now(UTC),
    )

    publisher.publish(event)

    assert publisher.events == [event]
    assert lifecycle_event_type(FeatureRuntimeState.READY) == FeatureEventType.LOADED
    assert lifecycle_event_type(FeatureRuntimeState.FAILED) == FeatureEventType.FAILED
