from collections import defaultdict
from decimal import Decimal

from .entities import TrendObservation

SOURCE_WEIGHTS: dict[str, Decimal] = {
    "search": Decimal("0.25"),
    "marketplace": Decimal("0.20"),
    "social": Decimal("0.20"),
    "editorial": Decimal("0.10"),
    "internal_behavior": Decimal("0.15"),
    "sales": Decimal("0.10"),
}


def aggregate_observations(
    observations: list[TrendObservation],
) -> dict[str, Decimal]:
    grouped: dict[str, list[TrendObservation]] = defaultdict(list)

    for observation in observations:
        grouped[observation.topic.lower().strip()].append(observation)

    result: dict[str, Decimal] = {}

    for topic, items in grouped.items():
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")

        for item in items:
            source_key = (
                item.source.value
                if hasattr(item.source, "value")
                else str(item.source)
            )
            weight = SOURCE_WEIGHTS.get(
                source_key,
                Decimal("0.05"),
            )

            weighted_sum += Decimal(str(item.value)) * weight
            total_weight += weight

        if total_weight > 0:
            result[topic] = weighted_sum / total_weight

    return result
