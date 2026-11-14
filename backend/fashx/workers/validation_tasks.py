"""Staging validation background tasks for Celery workers.

These tasks provide non-destructive, safe diagnostic verification of
queue routing, worker execution, retries, and dead-letter handling.
No user data, customer images, or sensitive payloads are accessed or stored.
"""

from datetime import UTC, datetime
from typing import Any

from celery import shared_task


@shared_task(
    name="fashx.validation.ping",
    ignore_result=True,
)
def staging_worker_ping() -> dict[str, Any]:
    """Lightweight vitality check for any connected worker."""
    return {
        "status": "ok",
        "completed_at": datetime.now(UTC).isoformat(),
    }


@shared_task(
    name="fashx.validation.ping_tryon",
    ignore_result=True,
)
def staging_tryon_ping() -> dict[str, Any]:
    """Diagnostic task explicitly routed to the 'tryon' queue."""
    return {
        "status": "ok",
        "queue": "tryon",
        "completed_at": datetime.now(UTC).isoformat(),
    }


@shared_task(
    name="fashx.validation.ping_ingest",
    ignore_result=True,
)
def staging_ingest_ping() -> dict[str, Any]:
    """Diagnostic task explicitly routed to the 'ingest' queue."""
    return {
        "status": "ok",
        "queue": "ingest",
        "completed_at": datetime.now(UTC).isoformat(),
    }


@shared_task(
    name="fashx.validation.ping_maintenance",
    ignore_result=True,
)
def staging_maintenance_ping() -> dict[str, Any]:
    """Diagnostic task explicitly routed to the 'maintenance' queue."""
    return {
        "status": "ok",
        "queue": "maintenance",
        "completed_at": datetime.now(UTC).isoformat(),
    }


@shared_task(
    name="fashx.validation.retryable",
    bind=True,
    max_retries=3,
    default_retry_delay=1,
)
def staging_retryable_task(self: Any, fail_count: int = 1) -> dict[str, Any]:
    """Diagnostic task designed to fail a controlled number of times before succeeding."""
    current_attempt = self.request.retries
    if current_attempt < fail_count:
        raise self.retry(
            exc=RuntimeError(f"Simulated transient error on attempt {current_attempt}"),
            countdown=1,
        )
    return {
        "status": "succeeded_after_retry",
        "attempts": current_attempt + 1,
        "completed_at": datetime.now(UTC).isoformat(),
    }


@shared_task(
    name="fashx.validation.fatal",
    bind=True,
    max_retries=0,
)
def staging_fatal_task(self: Any) -> None:
    """Diagnostic task that raises an unhandled error to verify dead-letter routing."""
    raise ValueError("Controlled diagnostic fatal failure for dead-letter testing")
