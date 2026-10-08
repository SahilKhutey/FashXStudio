from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.trends.entities import (
    Trend,
    TrendContext,
    TrendObservation,
    TrendSnapshot,
)
from fashx.domain.trends.enums import (
    SignalType,
    TrendDirection,
    TrendSource,
    TrendStatus,
)


def test_valid_observation():
    observation = TrendObservation(
        topic="oversized jacket",
        value=Decimal("100"),
    )
    observation.validate()
    assert observation.topic == "oversized jacket"
    assert observation.value == Decimal("100")
    assert observation.trend_type == "style"
    assert observation.signal_type == SignalType.ENGAGEMENT
    assert observation.source == TrendSource.CURATED


def test_observation_requires_topic():
    observation = TrendObservation(
        value=Decimal("100"),
    )
    with pytest.raises(ValidationError, match="topic is required"):
        observation.validate()


def test_observation_blank_topic_rejected():
    observation = TrendObservation(
        topic="   ",
        value=Decimal("100"),
    )
    with pytest.raises(ValidationError, match="topic is required"):
        observation.validate()


def test_negative_observation_rejected():
    observation = TrendObservation(
        topic="jacket",
        value=Decimal("-1"),
    )
    with pytest.raises(ValidationError, match="cannot be negative"):
        observation.validate()


def test_valid_trend():
    trend = Trend(
        topic="streetwear",
        strength=0.80,
        confidence=0.85,
        momentum=0.20,
    )
    trend.validate()
    assert trend.topic == "streetwear"
    assert trend.strength == 0.80
    assert trend.status == TrendStatus.DRAFT
    assert trend.direction == TrendDirection.STABLE


def test_trend_requires_topic():
    trend = Trend(
        topic="",
        strength=0.5,
    )
    with pytest.raises(ValidationError, match="Trend topic is required"):
        trend.validate()


def test_strength_bounds():
    trend = Trend(
        topic="streetwear",
        strength=1.50,
    )
    with pytest.raises(ValidationError, match="strength must be between 0 and 1"):
        trend.validate()

    trend_negative = Trend(
        topic="streetwear",
        strength=-0.1,
    )
    with pytest.raises(ValidationError, match="strength must be between 0 and 1"):
        trend_negative.validate()


def test_confidence_bounds():
    trend = Trend(
        topic="streetwear",
        confidence=1.1,
    )
    with pytest.raises(ValidationError, match="confidence must be between 0 and 1"):
        trend.validate()


def test_momentum_bounds():
    trend = Trend(
        topic="streetwear",
        momentum=1.5,
    )
    with pytest.raises(ValidationError, match="Momentum must be between -1 and 1"):
        trend.validate()

    trend_low = Trend(
        topic="streetwear",
        momentum=-1.5,
    )
    with pytest.raises(ValidationError, match="Momentum must be between -1 and 1"):
        trend_low.validate()


def test_observation_count_bounds():
    trend = Trend(
        topic="streetwear",
        observation_count=-1,
    )
    with pytest.raises(ValidationError, match="Observation count cannot be negative"):
        trend.validate()


def test_version_positive():
    trend = Trend(
        topic="streetwear",
        version=0,
    )
    with pytest.raises(ValidationError, match="Trend version must be positive"):
        trend.validate()


def test_validity_window_validation():
    now = datetime.now(UTC)
    invalid_trend = Trend(
        topic="streetwear",
        valid_from=now,
        valid_until=now - timedelta(days=1),
    )
    with pytest.raises(ValidationError, match="validity window is invalid"):
        invalid_trend.validate()

    valid_trend = Trend(
        topic="streetwear",
        valid_from=now,
        valid_until=now + timedelta(days=7),
    )
    valid_trend.validate()


def test_trend_touch():
    trend = Trend(topic="streetwear")
    initial_version = trend.version
    initial_updated = trend.updated_at
    trend.touch()
    assert trend.version == initial_version + 1
    assert trend.updated_at >= initial_updated


def test_trend_snapshot():
    tid = uuid4()
    snapshot = TrendSnapshot(
        trend_id=tid,
        topic="quiet luxury",
        region="IN",
        strength=0.88,
        momentum=0.45,
        confidence=0.92,
        direction=TrendDirection.RISING,
        observation_count=15,
    )
    assert snapshot.trend_id == tid
    assert snapshot.topic == "quiet luxury"
    assert snapshot.strength == 0.88
    assert snapshot.engine_version == "1.0.0"


def test_trend_context():
    context = TrendContext(
        region="IN",
        trend_type="style",
        limit=10,
    )
    assert context.region == "IN"
    assert context.limit == 10
