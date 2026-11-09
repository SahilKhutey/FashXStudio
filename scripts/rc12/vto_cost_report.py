"""RC12 VTO Productionization & Cost Accounting Monitor."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VTOCostSummary:
    total_jobs: int
    mock_jobs: int
    real_jobs: int
    failed_jobs: int
    total_spend_usd: float
    budget_usd: float
    budget_used_percent: float
    spend_warning_triggered: bool
    p95_latency_ms: float | None


def compile_vto_cost_report(
    jobs: list[dict[str, Any]],
    budget_usd: float = 350.0,
) -> VTOCostSummary:
    """Summarizes VTO job executions, mode provenance, spend accrual, and budget warnings."""
    total_jobs = len(jobs)
    mock_count = 0
    real_count = 0
    failed_count = 0
    total_spend = 0.0
    latencies: list[float] = []

    for job in jobs:
        status = job.get("status")
        mode = job.get("mode", "mock")

        if status == "failed":
            failed_count += 1

        if mode == "real":
            real_count += 1
            cost = job.get("cost_usd")
            if cost is not None and isinstance(cost, (int, float)):
                total_spend += float(cost)
        else:
            mock_count += 1

        lat = job.get("duration_ms")
        if lat is not None and isinstance(lat, (int, float)):
            latencies.append(float(lat))

    budget_ratio = (total_spend / budget_usd) if budget_usd > 0 else 0.0
    spend_warning = budget_ratio >= 0.80

    p95_lat: float | None = None
    if latencies:
        sorted_lat = sorted(latencies)
        k = math.ceil(0.95 * len(sorted_lat)) - 1
        p95_lat = sorted_lat[max(0, min(k, len(sorted_lat) - 1))]

    return VTOCostSummary(
        total_jobs=total_jobs,
        mock_jobs=mock_count,
        real_jobs=real_count,
        failed_jobs=failed_count,
        total_spend_usd=round(total_spend, 2),
        budget_usd=budget_usd,
        budget_used_percent=round(budget_ratio * 100.0, 1),
        spend_warning_triggered=spend_warning,
        p95_latency_ms=p95_lat,
    )
