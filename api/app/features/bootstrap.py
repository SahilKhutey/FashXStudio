"""Application-owned feature manager bootstrap."""

from .feature_catalog import FEATURE_CATALOG
from .foundation import FeatureConfig, FeatureConfigStore, FeatureManager


def create_feature_manager(feature_flags: dict[str, bool] | None = None) -> FeatureManager:
    configs = {
        feature_id: FeatureConfig(enabled=enabled)
        for feature_id, enabled in (feature_flags or {}).items()
    }
    manager = FeatureManager(config=FeatureConfigStore(configs))
    for feature in FEATURE_CATALOG:
        manager.register(feature)
    return manager
