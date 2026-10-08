from datetime import UTC, datetime

import pytest

from fashx.domain.analytics.aggregation import (
    event_dimensions,
    truncate_timestamp,
)
from fashx.domain.analytics.entities import AnalyticsEvent
from fashx.domain.analytics.enums import (
    AggregationPeriod,
    AnalyticsEventType,
)


def test_minute_truncation():
    timestamp = datetime(2026, 9, 16, 14, 33, 45, 123456, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.MINUTE)
    assert result.second == 0
    assert result.microsecond == 0
    assert result.minute == 33
    assert result.hour == 14


def test_hour_truncation():
    timestamp = datetime(2026, 9, 16, 14, 33, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.HOUR)
    assert result.hour == 14
    assert result.minute == 0
    assert result.second == 0


def test_day_truncation():
    timestamp = datetime(2026, 9, 16, 14, 33, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.DAY)
    assert result.day == 16
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


def test_week_truncation():
    # 2026-09-16 is a Wednesday (weekday 2). The preceding Monday is 2026-09-14.
    timestamp = datetime(2026, 9, 16, 14, 33, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.WEEK)
    assert result.year == 2026
    assert result.month == 9
    assert result.day == 14
    assert result.hour == 0
    assert result.minute == 0
    assert result.weekday() == 0  # Monday


def test_week_truncation_crossing_month():
    # 2026-10-02 is a Friday (weekday 4). Preceding Monday is 2026-09-28.
    timestamp = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.WEEK)
    assert result.year == 2026
    assert result.month == 9
    assert result.day == 28
    assert result.weekday() == 0


def test_month_truncation():
    timestamp = datetime(2026, 9, 16, 14, 33, tzinfo=UTC)
    result = truncate_timestamp(timestamp, AggregationPeriod.MONTH)
    assert result.year == 2026
    assert result.month == 9
    assert result.day == 1
    assert result.hour == 0


def test_unsupported_period():
    timestamp = datetime(2026, 9, 16, 14, 33, tzinfo=UTC)
    with pytest.raises(ValueError, match="Unsupported period"):
        truncate_timestamp(timestamp, "decade")  # type: ignore


def test_event_dimensions_extraction():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        session_id="s1",
        region="IN",
        category="jackets",
        brand="Levi's",
    )
    dims = event_dimensions(event)
    assert dims == {
        "region": "IN",
        "category": "jackets",
        "brand": "Levi's",
    }

    event_empty = AnalyticsEvent(
        event_type=AnalyticsEventType.PAGE_VIEWED,
        session_id="s1",
    )
    assert event_dimensions(event_empty) == {}
