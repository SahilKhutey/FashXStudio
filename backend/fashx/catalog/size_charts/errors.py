"""Typed domain exceptions for Phase 08.1 Product Size Data."""

from __future__ import annotations


class SizeChartError(Exception):
    """Base exception for all product size data errors."""

    pass


class SizeChartValidationError(SizeChartError, ValueError):
    """Raised when an incoming chart fails schema, category, or range validation."""

    pass


class SizeChartNotFoundError(SizeChartError):
    """Raised when no size chart exists for the requested merchant product."""

    pass


class SizeChartUnauthorizedError(SizeChartError):
    """Raised when a source is not authorized to submit charts for a merchant product."""

    pass


class SizeChartQuarantineError(SizeChartError):
    """Raised when an incoming chart contains ambiguous or conflicting data requiring quarantine."""

    pass


class SizeChartStaleError(SizeChartError):
    """Raised when a chart has exceeded its freshness SLA."""

    pass
