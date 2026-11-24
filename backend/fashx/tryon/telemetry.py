"""Lifecycle Metrics and Cost Telemetry for Virtual Try-On (Phase 07.4)."""

from __future__ import annotations

from datetime import datetime

from fashx.core.metrics import emit_metric


def record_tryon_lifecycle_latencies(
    *,
    environment: str = "dev",
    provider: str = "fashn_api",
    model: str = "tryon-v1.6",
    outcome: str = "success",
    created_at: datetime | None = None,
    started_at: datetime | None = None,
    provider_submitted_at: datetime | None = None,
    provider_completed_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> dict[str, float]:
    """Calculates and emits non-identifying lifecycle latency metrics.

    Dimensions:
    - environment (low-cardinality)
    - provider (low-cardinality)
    - model (low-cardinality)
    - outcome (success | failure)

    Never logs user IDs, product IDs, or asset keys.
    """
    dimensions = {
        "Provider": provider,
        "Model": model,
        "Outcome": outcome,
    }
    latencies: dict[str, float] = {}

    # Queue wait latency: T_worker_started - T_accepted
    if created_at and started_at and started_at >= created_at:
        t_queue = (started_at - created_at).total_seconds()
        latencies["queue_wait_seconds"] = t_queue
        emit_metric(
            "VTOQueueWaitDuration",
            t_queue,
            "Seconds",
            service="tryon",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/VTO",
        )

    # Provider inference latency: T_provider_completed - T_provider_submitted
    if provider_submitted_at and provider_completed_at and provider_completed_at >= provider_submitted_at:
        t_provider = (provider_completed_at - provider_submitted_at).total_seconds()
        latencies["provider_latency_seconds"] = t_provider
        emit_metric(
            "VTOProviderLatency",
            t_provider,
            "Seconds",
            service="tryon",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/VTO",
        )

    # End-to-end latency: T_completed - T_accepted
    if created_at and completed_at and completed_at >= created_at:
        t_e2e = (completed_at - created_at).total_seconds()
        latencies["end_to_end_seconds"] = t_e2e
        emit_metric(
            "VTOEndToEndDuration",
            t_e2e,
            "Seconds",
            service="tryon",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/VTO",
        )

    return latencies
