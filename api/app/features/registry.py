"""HTTP-facing view of the executable Feature Foundation catalog."""

from schemas.features.v1 import FeatureDomain, FeatureStatus, FeatureSummary

from .feature_catalog import FEATURE_CATALOG
from .foundation import FeatureDefinition


class FeatureRegistry:
    def list(self, domain: FeatureDomain | None = None) -> list[FeatureSummary]:
        features = [self._summary(feature) for feature in FEATURE_CATALOG]
        return [feature for feature in features if domain is None or feature.domain == domain]

    def get(self, feature_id: str) -> FeatureSummary | None:
        return next((feature for feature in self.list() if feature.id == feature_id), None)

    @staticmethod
    def _summary(feature: FeatureDefinition) -> FeatureSummary:
        phase = int(feature.feature_id.removeprefix("FX-F"))
        status = FeatureStatus.ENABLED if phase <= 14 else FeatureStatus.PLANNED
        return FeatureSummary(
            id=feature.feature_id,
            name=feature.name,
            version=feature.version,
            domain=FeatureDomain.PLATFORM if phase <= 1 else FeatureDomain.USER,
            status=status,
            description=feature.description,
            depends_on=list(feature.dependencies),
            required_core_capabilities=list(feature.capabilities),
            routes=list(feature.routes),
            events=[],
            default_enabled=feature.enabled,
        )
