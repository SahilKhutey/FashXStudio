"""Feature availability rules shared by API routes and future clients."""

from schemas.features.v1 import FeatureAvailability, FeatureStatus, FeatureSummary

from .registry import FeatureRegistry


class FeatureAvailabilityService:
    def __init__(self, registry: FeatureRegistry | None = None) -> None:
        self.registry = registry or FeatureRegistry()

    def list_features(self) -> list[FeatureSummary]:
        return self.registry.list()

    def availability(self, feature_id: str) -> FeatureAvailability | None:
        feature = self.registry.get(feature_id)
        if feature is None:
            return None

        reasons: list[str] = []
        if feature.status != FeatureStatus.ENABLED:
            reasons.append(f"Feature status is '{feature.status}'.")
        for dependency_id in feature.depends_on:
            dependency = self.registry.get(dependency_id)
            if dependency is None or dependency.status != FeatureStatus.ENABLED:
                reasons.append(f"Dependency '{dependency_id}' is not enabled.")
        return FeatureAvailability(
            feature=feature,
            available=not reasons,
            unavailable_reasons=reasons,
        )
