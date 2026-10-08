"""HTTP discovery surface for feature-aware clients and internal tooling."""

from fastapi import APIRouter

from api.app.core.errors import EntityNotFoundError
from api.app.core.settings import get_settings
from schemas.features.v1 import FeatureAvailability, FeatureRuntimeSnapshot, FeatureSummary

from .application import FeatureAvailabilityService
from .runtime import FeatureRuntime

router = APIRouter(prefix="/features", tags=["features"])


@router.get("", response_model=list[FeatureSummary])
async def list_features() -> list[FeatureSummary]:
    return FeatureAvailabilityService().list_features()


@router.get("/runtime", response_model=list[FeatureRuntimeSnapshot])
async def initialize_feature_runtime() -> list[FeatureRuntimeSnapshot]:
    runtime = FeatureRuntime(FeatureAvailabilityService(), get_settings().feature_flags)
    return [
        snapshot
        for feature in FeatureAvailabilityService().list_features()
        if (snapshot := runtime.initialize(feature.id)) is not None
    ]


@router.get("/{feature_id}", response_model=FeatureAvailability)
async def get_feature_availability(feature_id: str) -> FeatureAvailability:
    availability = FeatureAvailabilityService().availability(feature_id)
    if availability is None:
        raise EntityNotFoundError("Feature", feature_id)
    return availability
