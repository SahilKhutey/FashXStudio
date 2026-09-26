from decimal import Decimal

from .entities import AnalyticsMetric
from .enums import AggregationPeriod, MetricType


def calculate_rate(
    numerator: Decimal | int,
    denominator: Decimal | int,
) -> Decimal:
    den = Decimal(str(denominator))
    if den <= Decimal("0"):
        return Decimal("0.00")
    num = Decimal(str(numerator))
    return num / den


__all__ = [
    "AggregationPeriod",
    "AnalyticsMetric",
    "MetricType",
    "calculate_rate",
]
