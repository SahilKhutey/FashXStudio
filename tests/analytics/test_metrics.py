from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from app.domain.analytics.entities import (
    AggregationBucket,
    AnalyticsMetric,
)
from app.domain.analytics.enums import (
    AggregationPeriod,
    MetricType,
)
from app.domain.analytics.metrics import calculate_rate


def test_valid_metric():
    metric = AnalyticsMetric(
        name="product_views",
        metric_type=MetricType.COUNT,
        value=Decimal("1248"),
        period=AggregationPeriod.DAY,
        period_start=datetime.now(UTC),
        dimensions={"region": "IN", "category": "footwear"},
    )
    metric.validate()
    assert metric.name == "product_views"
    assert metric.value == Decimal("1248")
    assert metric.metric_type == MetricType.COUNT


def test_metric_name_required():
    metric = AnalyticsMetric(
        name="",
        metric_type=MetricType.COUNT,
        value=Decimal("10"),
        period=AggregationPeriod.DAY,
        period_start=datetime.now(UTC),
    )
    with pytest.raises(ValidationError, match="Metric name is required"):
        metric.validate()


def test_metric_negative_value_rejected():
    metric = AnalyticsMetric(
        name="bounce_rate",
        metric_type=MetricType.RATE,
        value=Decimal("-0.5"),
        period=AggregationPeriod.DAY,
        period_start=datetime.now(UTC),
    )
    with pytest.raises(ValidationError, match="cannot be negative"):
        metric.validate()


def test_aggregation_bucket_add():
    bucket = AggregationBucket(
        metric_name="order_revenue",
        period=AggregationPeriod.DAY,
        period_start=datetime.now(UTC),
        dimensions={"region": "IN"},
    )
    assert bucket.count == 0
    assert bucket.total_value == Decimal("0.00")

    bucket.add(Decimal("1500.50"))
    assert bucket.count == 1
    assert bucket.total_value == Decimal("1500.50")

    bucket.add(Decimal("499.50"))
    assert bucket.count == 2
    assert bucket.total_value == Decimal("2000.00")

    bucket.add(None)
    assert bucket.count == 3
    assert bucket.total_value == Decimal("2000.00")


def test_calculate_rate():
    assert calculate_rate(50, 200) == Decimal("0.25")
    assert calculate_rate(0, 100) == Decimal("0.00")
    assert calculate_rate(10, 0) == Decimal("0.00")
