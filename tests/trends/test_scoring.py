import pytest

from fashx.domain.trends.enums import TrendDirection
from fashx.domain.trends.scoring import (
    direction_from_momentum,
    momentum_score,
    normalize,
    trend_strength,
)


def test_positive_momentum():
    result = momentum_score(120, 100)
    assert pytest.approx(result, 0.001) == 0.2


def test_declining_momentum():
    result = momentum_score(80, 100)
    assert pytest.approx(result, 0.001) == -0.2


def test_zero_momentum():
    result = momentum_score(100, 100)
    assert result == 0.0


def test_momentum_division_by_zero():
    assert momentum_score(50, 0) == 1.0
    assert momentum_score(0, 0) == 0.0


def test_momentum_clamping():
    assert momentum_score(500, 100) == 1.0
    assert momentum_score(0, 100) == -1.0


def test_rising_direction():
    assert direction_from_momentum(0.50) == TrendDirection.RISING
    assert direction_from_momentum(0.11) == TrendDirection.RISING


def test_stable_direction():
    assert direction_from_momentum(0.05) == TrendDirection.STABLE
    assert direction_from_momentum(0.10) == TrendDirection.STABLE
    assert direction_from_momentum(-0.10) == TrendDirection.STABLE
    assert direction_from_momentum(0.0) == TrendDirection.STABLE


def test_declining_direction():
    assert direction_from_momentum(-0.50) == TrendDirection.DECLINING
    assert direction_from_momentum(-0.11) == TrendDirection.DECLINING


def test_normalize():
    assert normalize(5000, 10000) == 0.5
    assert normalize(15000, 10000) == 1.0
    assert normalize(-10, 100) == 0.0
    assert normalize(100, 0) == 0.0
    assert normalize(100, -50) == 0.0


def test_trend_strength():
    strength = trend_strength(signal=0.8, momentum=0.2, confidence=0.9)
    # momentum_component = (0.2 + 1.0) / 2.0 = 0.6
    # 0.50 * 0.8 + 0.30 * 0.6 + 0.20 * 0.9 = 0.40 + 0.18 + 0.18 = 0.76
    assert pytest.approx(strength, 0.001) == 0.76


def test_trend_strength_clamping():
    assert trend_strength(1.0, 1.0, 1.0) <= 1.0
    assert trend_strength(0.0, -1.0, 0.0) >= 0.0
