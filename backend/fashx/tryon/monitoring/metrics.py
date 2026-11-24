"""Prometheus and CloudWatch metrics emitters for VTO caching and cost controls.

Strict PII Invariants:
Metric dimensions must be strictly low-cardinality and non-PII.
NEVER include user_id, product_id, image_hashes, or specific storage URIs in metric labels.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from fashx.core.metrics import emit_metric

logger = logging.getLogger(__name__)


def record_cache_lookup(outcome: str, provider: str = "fashn") -> None:
    """Record a cache lookup result (hit, miss, expired, invalidated)."""
    dimensions = {
        "Provider": provider.lower().strip(),
        "Outcome": outcome.lower().strip(),
    }
    emit_metric("TryOnCacheLookups", 1.0, unit="Count", dimensions=dimensions)


def record_provider_charge(
    provider: str,
    operation: str,
    amount_usd: Decimal,
    status: str,
) -> None:
    """Record a provider financial expenditure in USD."""
    dimensions = {
        "Provider": provider.lower().strip(),
        "Operation": operation.upper().strip(),
        "Status": status.upper().strip(),
    }
    emit_metric(
        "TryOnProviderSpendUSD",
        float(amount_usd),
        unit="None",
        dimensions=dimensions,
    )


def record_rate_limit_rejection(limit_type: str) -> None:
    """Record a rate limiting or concurrency rejection event."""
    dimensions = {
        "LimitType": limit_type.upper().strip(),
    }
    emit_metric("TryOnRateLimitRejections", 1.0, unit="Count", dimensions=dimensions)


def record_budget_reservation(scope_type: str, status: str, amount_usd: Decimal) -> None:
    """Record a budget reservation lifecycle event (reserved, committed, released)."""
    dimensions = {
        "ScopeType": scope_type.upper().strip(),
        "Status": status.upper().strip(),
    }
    emit_metric(
        "TryOnBudgetReservations",
        float(amount_usd),
        unit="None",
        dimensions=dimensions,
    )


def record_budget_utilization(scope_type: str, utilization_pct: Decimal) -> None:
    """Record the percentage utilization of an active budget."""
    dimensions = {
        "ScopeType": scope_type.upper().strip(),
    }
    emit_metric(
        "TryOnBudgetUtilizationPct",
        float(utilization_pct),
        unit="Percent",
        dimensions=dimensions,
    )
