from decimal import Decimal

from fashx.domain.trends.aggregation import aggregate_observations
from fashx.domain.trends.entities import TrendObservation
from fashx.domain.trends.enums import SignalType, TrendSource


def test_aggregate_observations_single_topic():
    observations = [
        TrendObservation(
            topic="oversized jacket",
            source=TrendSource.SEARCH,
            value=Decimal("100"),
        ),
        TrendObservation(
            topic="oversized jacket",
            source=TrendSource.MARKETPLACE,
            value=Decimal("200"),
        ),
    ]
    # search weight = 0.25, marketplace weight = 0.20
    # sum = 100 * 0.25 + 200 * 0.20 = 25 + 40 = 65
    # total_weight = 0.45
    # expected = 65 / 0.45 = 144.444...
    results = aggregate_observations(observations)
    assert "oversized jacket" in results
    expected = Decimal("65") / Decimal("0.45")
    assert results["oversized jacket"] == expected


def test_aggregate_observations_case_insensitive_and_whitespace():
    observations = [
        TrendObservation(
            topic=" Streetwear ",
            source=TrendSource.SEARCH,
            value=Decimal("50"),
        ),
        TrendObservation(
            topic="streetwear",
            source=TrendSource.SEARCH,
            value=Decimal("100"),
        ),
    ]
    results = aggregate_observations(observations)
    assert len(results) == 1
    assert "streetwear" in results
    assert results["streetwear"] == Decimal("75")


def test_aggregate_observations_multiple_topics():
    observations = [
        TrendObservation(
            topic="cargo pants",
            source=TrendSource.SOCIAL,
            value=Decimal("80"),
        ),
        TrendObservation(
            topic="silver jewelry",
            source=TrendSource.EDITORIAL,
            value=Decimal("90"),
        ),
    ]
    results = aggregate_observations(observations)
    assert len(results) == 2
    assert "cargo pants" in results
    assert "silver jewelry" in results
    assert results["cargo pants"] == Decimal("80")
    assert results["silver jewelry"] == Decimal("90")


def test_aggregate_observations_empty():
    assert aggregate_observations([]) == {}


def test_aggregate_observations_default_weight():
    # imported source has default 0.05 weight
    observations = [
        TrendObservation(
            topic="leather boots",
            source=TrendSource.IMPORTED,
            signal_type=SignalType.CLICKS,
            value=Decimal("120"),
        ),
    ]
    results = aggregate_observations(observations)
    assert results["leather boots"] == Decimal("120")
