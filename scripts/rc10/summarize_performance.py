"""RC10 performance profiling and metrics summarization utility."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LatencySummary:
    count: int
    min_ms: float
    max_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


def summarize_latencies(durations_ms: Sequence[float]) -> LatencySummary:
    """Summarizes a sequence of call durations into standard percentile metrics."""
    if not durations_ms:
        return LatencySummary(
            count=0,
            min_ms=0.0,
            max_ms=0.0,
            mean_ms=0.0,
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
        )

    sorted_vals = sorted(durations_ms)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        d = k - f
        return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * d

    return LatencySummary(
        count=n,
        min_ms=sorted_vals[0],
        max_ms=sorted_vals[-1],
        mean_ms=sum(sorted_vals) / n,
        p50_ms=percentile(0.50),
        p95_ms=percentile(0.95),
        p99_ms=percentile(0.99),
    )
