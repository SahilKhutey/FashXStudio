from .enums import TrendDirection


def normalize(
    value: float,
    maximum: float,
) -> float:
    if maximum <= 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            value / maximum,
        ),
    )


def momentum_score(
    current: float,
    previous: float,
) -> float:
    epsilon = 1e-9

    if previous <= epsilon:
        return (
            1.0
            if current > 0
            else 0.0
        )

    change = (
        current - previous
    ) / previous

    return max(
        -1.0,
        min(1.0, change),
    )


def direction_from_momentum(
    momentum: float,
) -> TrendDirection:
    if momentum > 0.10:
        return TrendDirection.RISING

    if momentum < -0.10:
        return TrendDirection.DECLINING

    return TrendDirection.STABLE


def trend_strength(
    signal: float,
    momentum: float,
    confidence: float,
) -> float:
    momentum_component = (
        (momentum + 1.0) / 2.0
    )

    result = (
        0.50 * signal
        + 0.30 * momentum_component
        + 0.20 * confidence
    )

    return max(
        0.0,
        min(1.0, result),
    )
