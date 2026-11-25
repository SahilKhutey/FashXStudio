"""Controlled enumerations for Phase 08.1 Product Size Data."""

from __future__ import annotations

from enum import Enum


class SizeChartStatus(str, Enum):
    """Lifecycle and verification status of a merchant size chart."""

    AVAILABLE = "AVAILABLE"
    VERIFIED = "VERIFIED"  # Backward compatibility with Phase 07.8
    MISSING = "MISSING"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNVERIFIED = "UNVERIFIED"
    STALE = "STALE"
    WITHDRAWN = "WITHDRAWN"


class MeasurementBasis(str, Enum):
    """Whether measurements describe the human body or the finished physical garment."""

    BODY = "BODY"
    GARMENT = "GARMENT"
    UNKNOWN = "UNKNOWN"


class MeasurementUnit(str, Enum):
    """Supported physical measurement units for linear dimensions."""

    CM = "CM"
    MM = "MM"
    IN = "IN"
    INCH = "INCH"  # Backward compatibility with Phase 07.8


class AvailabilityStatus(str, Enum):
    """Inventory and purchasable availability state for a product variant."""

    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"
    DISCONTINUED = "DISCONTINUED"
    DELISTED = "DELISTED"
    TAKEDOWN = "TAKEDOWN"
    PREORDER = "PREORDER"


class MappingStatus(str, Enum):
    """Verification status of a size label mapping across systems."""

    NATIVE = "NATIVE"
    VERIFIED = "VERIFIED"
    VERIFIED_MAPPING = "VERIFIED_MAPPING"
    UNMAPPED = "UNMAPPED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ChangeEventType(str, Enum):
    """Audit events recorded during size chart lifecycle changes."""

    CHART_CREATED = "CHART_CREATED"
    VERSION_INCREMENTED = "VERSION_INCREMENTED"
    NO_OP_UNCHANGED = "NO_OP_UNCHANGED"
    SIZE_CHART_CREATED = "SIZE_CHART_CREATED"
    SIZE_CHART_UPDATED = "SIZE_CHART_UPDATED"
    SIZE_CHART_WITHDRAWN = "SIZE_CHART_WITHDRAWN"
    SIZE_CHART_QUARANTINED = "SIZE_CHART_QUARANTINED"
    SIZE_CHART_RETRIEVED = "SIZE_CHART_RETRIEVED"
    AVAILABILITY_CHANGED = "AVAILABILITY_CHANGED"
