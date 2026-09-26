from datetime import UTC, datetime, timedelta

from .entities import AnalyticsEvent
from .enums import AggregationPeriod


def truncate_timestamp(
    timestamp: datetime,
    period: AggregationPeriod,
) -> datetime:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)

    if period == AggregationPeriod.MINUTE:
        return timestamp.replace(
            second=0,
            microsecond=0,
        )

    if period == AggregationPeriod.HOUR:
        return timestamp.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == AggregationPeriod.DAY:
        return timestamp.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == AggregationPeriod.WEEK:
        day = timestamp.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return day - timedelta(days=day.weekday())

    if period == AggregationPeriod.MONTH:
        return timestamp.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    raise ValueError(f"Unsupported period: {period}")


def event_dimensions(
    event: AnalyticsEvent,
) -> dict[str, str]:
    dimensions: dict[str, str] = {}

    if event.region:
        dimensions["region"] = event.region

    if event.category:
        dimensions["category"] = event.category

    if event.brand:
        dimensions["brand"] = event.brand

    return dimensions
