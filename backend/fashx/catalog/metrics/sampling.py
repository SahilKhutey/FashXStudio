from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable
from typing import Any


def reproducible_sample[T](
    items: list[T],
    sample_size: int,
    random_seed: int = 42,
) -> list[T]:
    """Deterministically sample a fixed number of items using a reproducible seed."""
    if not items or sample_size <= 0:
        return []
    if len(items) <= sample_size:
        return list(items)

    rng = random.Random(random_seed)
    # Sample without replacement
    return rng.sample(items, sample_size)


def stratified_sample[T](
    items: list[T],
    sample_size: int,
    group_key: Callable[[T], Any],
    random_seed: int = 42,
) -> list[T]:
    """Deterministically select a stratified random sample grouped by a key."""
    if not items or sample_size <= 0:
        return []
    if len(items) <= sample_size:
        return list(items)

    # Partition items by stratum
    strata: dict[Any, list[T]] = defaultdict(list)
    for item in items:
        strata[group_key(item)].append(item)

    rng = random.Random(random_seed)
    sampled: list[T] = []

    # Calculate proportional allocation per stratum
    total_items = len(items)
    for _key, group in sorted(strata.items(), key=lambda x: str(x[0])):
        stratum_quota = max(1, round((len(group) / total_items) * sample_size))
        take_count = min(len(group), stratum_quota)
        sampled.extend(rng.sample(group, take_count))

    # Adjust to exact sample_size if rounding produced discrepancy
    if len(sampled) > sample_size:
        sampled = rng.sample(sampled, sample_size)
    elif len(sampled) < sample_size:
        remaining = [x for x in items if x not in set(sampled)]
        needed = sample_size - len(sampled)
        if remaining:
            sampled.extend(rng.sample(remaining, min(len(remaining), needed)))

    return sampled
