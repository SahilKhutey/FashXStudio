"""Worker telemetry and Celery operational metric emitters for FashXStudio."""

from __future__ import annotations

import logging
from typing import Any

from fashx.core.metrics import emit_metric

logger = logging.getLogger("fashx.workers.telemetry")


def emit_worker_heartbeat(
    worker_type: str,
    environment: str = "dev",
) -> dict[str, Any]:
    """Emit periodic worker heartbeat metric to CloudWatch EMF."""
    return emit_metric(
        "WorkerHeartbeat",
        1.0,
        unit="Count",
        service=f"worker-{worker_type}",
        environment=environment,
        dimensions={"WorkerType": worker_type},
        namespace="FashX/Workers",
    )


def emit_queue_depth(
    queue_name: str,
    depth: int,
    environment: str = "dev",
) -> dict[str, Any]:
    """Emit current Celery/Redis queue depth metric to CloudWatch EMF."""
    return emit_metric(
        "QueueDepth",
        float(depth),
        unit="Count",
        service="worker",
        environment=environment,
        dimensions={"Queue": queue_name},
        namespace="FashX/Queues",
    )


def emit_task_lifecycle_metric(
    event: str,
    task_name: str,
    queue: str,
    duration_ms: float | None = None,
    retry_count: int = 0,
    outcome: str = "success",
    environment: str = "dev",
) -> None:
    """Publish Celery task lifecycle metric events."""
    safe_task = task_name.split(".")[-1]
    dimensions = {
        "Task": safe_task,
        "Queue": queue,
        "Outcome": outcome,
    }

    if event == "started":
        emit_metric(
            "TaskStarted",
            1.0,
            unit="Count",
            service="worker",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/Workers",
        )
    elif event == "succeeded":
        emit_metric(
            "TaskSucceeded",
            1.0,
            unit="Count",
            service="worker",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/Workers",
        )
        if duration_ms is not None:
            emit_metric(
                "TaskDuration",
                duration_ms,
                unit="Milliseconds",
                service="worker",
                environment=environment,
                dimensions=dimensions,
                namespace="FashX/Workers",
            )
    elif event == "failed":
        emit_metric(
            "TaskFailed",
            1.0,
            unit="Count",
            service="worker",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/Workers",
        )
        if duration_ms is not None:
            emit_metric(
                "TaskDuration",
                duration_ms,
                unit="Milliseconds",
                service="worker",
                environment=environment,
                dimensions=dimensions,
                namespace="FashX/Workers",
            )
    elif event == "retried":
        emit_metric(
            "TaskRetried",
            1.0,
            unit="Count",
            service="worker",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/Workers",
        )
    elif event == "dead_lettered":
        emit_metric(
            "TaskDeadLettered",
            1.0,
            unit="Count",
            service="worker",
            environment=environment,
            dimensions=dimensions,
            namespace="FashX/Workers",
        )
