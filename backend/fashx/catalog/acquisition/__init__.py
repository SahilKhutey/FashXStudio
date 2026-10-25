"""Automated catalog acquisition, source adapter layer, and normalization pipeline."""

from fashx.catalog.acquisition.contract import (
    AcquisitionBatch,
    CatalogSourceAdapter,
    SourceProduct,
)
from fashx.catalog.acquisition.image_validator import (
    ImageValidationResult,
    SafeImageValidator,
)
from fashx.catalog.acquisition.normalizer import CatalogNormalizer
from fashx.catalog.acquisition.pipeline import (
    AcquisitionPipeline,
    PipelineRunReport,
)
from fashx.catalog.acquisition.registry import (
    AdapterRegistry,
    SourceConfig,
    get_adapter_registry,
)
from fashx.catalog.acquisition.sync_service import CatalogSyncService

__all__ = [
    "AcquisitionBatch",
    "AcquisitionPipeline",
    "AdapterRegistry",
    "CatalogNormalizer",
    "CatalogSourceAdapter",
    "CatalogSyncService",
    "ImageValidationResult",
    "PipelineRunReport",
    "SafeImageValidator",
    "SourceConfig",
    "SourceProduct",
    "get_adapter_registry",
]
