"""Size charts module for Phase 08.1 Product Size Data, Revisions, and Availability."""

from fashx.catalog.size_charts.availability import VariantAvailabilityService
from fashx.catalog.size_charts.enums import (
    AvailabilityStatus,
    ChangeEventType,
    MappingStatus,
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.errors import (
    SizeChartError,
    SizeChartNotFoundError,
    SizeChartQuarantineError,
    SizeChartStaleError,
    SizeChartUnauthorizedError,
    SizeChartValidationError,
)
from fashx.catalog.size_charts.fingerprint import compute_size_chart_fingerprint
from fashx.catalog.size_charts.freshness import FreshnessPolicy
from fashx.catalog.size_charts.measurement_fields import FIELD_DEFINITIONS
from fashx.catalog.size_charts.repository import ProductSizeChartRepository, SizeChartRepository
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    ProductSizeChartResponse,
    ProductVariantAvailability,
    SizeChartRevisionCreate,
    SizeChartRevisionSummary,
    SizeChartRow,
    SizeChartRowResponse,
    SizeChartUnavailableResponse,
    SizeMeasurement,
    SizeMeasurementResponse,
    SizeSystemRef,
    SourceProvenance,
    VariantStockItem,
)
from fashx.catalog.size_charts.service import (
    SizeChartService,
)
from fashx.catalog.size_charts.size_systems import SYSTEMS, map_size_label, normalize_size_label
from fashx.catalog.size_charts.units import normalize_to_cm
from fashx.catalog.size_charts.validation import validate_chart

__all__ = [
    "AvailabilityStatus",
    "ChangeEventType",
    "FIELD_DEFINITIONS",
    "FreshnessPolicy",
    "MappingStatus",
    "MeasurementBasis",
    "MeasurementUnit",
    "MerchantSizeChartResponse",
    "ProductSizeChartRepository",
    "ProductSizeChartResponse",
    "ProductVariantAvailability",
    "SYSTEMS",
    "SizeChartError",
    "SizeChartNotFoundError",
    "SizeChartQuarantineError",
    "SizeChartRepository",
    "SizeChartRevisionCreate",
    "SizeChartRevisionSummary",
    "SizeChartRow",
    "SizeChartRowResponse",
    "SizeChartService",
    "SizeChartStaleError",
    "SizeChartStatus",
    "SizeChartUnauthorizedError",
    "SizeChartUnavailableResponse",
    "SizeChartValidationError",
    "SizeMeasurement",
    "SizeMeasurementResponse",
    "SizeSystemRef",
    "SourceProvenance",
    "VariantAvailabilityService",
    "VariantStockItem",
    "compute_size_chart_fingerprint",
    "map_size_label",
    "normalize_size_label",
    "normalize_to_cm",
    "validate_chart",
]
