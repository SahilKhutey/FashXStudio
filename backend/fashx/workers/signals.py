"""Celery signal handlers for distributed trace propagation and task lifecycle telemetry."""

from __future__ import annotations

import logging
import time
from typing import Any

from fashx.core.observability import clear_request_context, set_request_context
from fashx.core.settings import get_settings
from fashx.core.tracing import extract_trace_id
from fashx.workers.telemetry import emit_task_lifecycle_metric

logger = logging.getLogger("fashx.workers.signals")

# In-memory dictionary tracking task start times per task_id
_TASK_START_TIMES: dict[str, float] = {}


def register_celery_signals(celery_app: Any) -> None:
    """Register Celery signal handlers on the application instance."""
    try:
        from celery.signals import (
            task_failure,
            task_postrun,
            task_prerun,
            task_retry,
            task_success,
        )
    except ImportError:
        logger.debug("Celery not installed; skipping signal registration")
        return

    @task_prerun.connect
    def on_task_prerun(
        task_id: str,
        task: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        **_: Any,
    ) -> None:
        _TASK_START_TIMES[task_id] = time.perf_counter()
        headers = getattr(task.request, "headers", None) or {}

        request_id = headers.get("request_id")
        traceparent = headers.get("traceparent")
        trace_id = extract_trace_id(traceparent) if traceparent else None

        set_request_context(request_id, trace_id)

        queue = "unknown"
        if hasattr(task.request, "delivery_info") and task.request.delivery_info:
            queue = task.request.delivery_info.get("routing_key", "unknown")

        settings = get_settings()
        emit_task_lifecycle_metric(
            event="started",
            task_name=task.name,
            queue=queue,
            environment=getattr(settings, "env", "dev"),
        )
        logger.info(
            "task_started",
            extra={
                "event": "task_started",
                "task_id": task_id,
                "task_name": task.name,
                "queue": queue,
                "request_id": request_id,
                "trace_id": trace_id,
            },
        )

    @task_success.connect
    def on_task_success(sender: Any, result: Any, **_: Any) -> None:
        task = sender
        task_id = getattr(task.request, "id", "unknown")
        start_time = _TASK_START_TIMES.pop(task_id, None)
        duration_ms = (
            round((time.perf_counter() - start_time) * 1000, 2)
            if start_time
            else None
        )

        queue = "unknown"
        if hasattr(task.request, "delivery_info") and task.request.delivery_info:
            queue = task.request.delivery_info.get("routing_key", "unknown")

        settings = get_settings()
        emit_task_lifecycle_metric(
            event="succeeded",
            task_name=task.name,
            queue=queue,
            duration_ms=duration_ms,
            outcome="success",
            environment=getattr(settings, "env", "dev"),
        )
        logger.info(
            "task_succeeded",
            extra={
                "event": "task_succeeded",
                "task_id": task_id,
                "task_name": task.name,
                "queue": queue,
                "duration_ms": duration_ms,
            },
        )

    @task_failure.connect
    def on_task_failure(
        task_id: str,
        exception: Exception,
        sender: Any,
        **_: Any,
    ) -> None:
        task = sender
        start_time = _TASK_START_TIMES.pop(task_id, None)
        duration_ms = (
            round((time.perf_counter() - start_time) * 1000, 2)
            if start_time
            else None
        )

        queue = "unknown"
        if hasattr(task.request, "delivery_info") and task.request.delivery_info:
            queue = task.request.delivery_info.get("routing_key", "unknown")

        settings = get_settings()
        emit_task_lifecycle_metric(
            event="failed",
            task_name=task.name,
            queue=queue,
            duration_ms=duration_ms,
            outcome="failure",
            environment=getattr(settings, "env", "dev"),
        )
        logger.error(
            "task_failed",
            extra={
                "event": "task_failed",
                "task_id": task_id,
                "task_name": task.name,
                "queue": queue,
                "error_type": type(exception).__name__,
                "duration_ms": duration_ms,
            },
        )

    @task_retry.connect
    def on_task_retry(
        request: Any,
        reason: Exception,
        sender: Any,
        **_: Any,
    ) -> None:
        task = sender
        task_id = getattr(request, "id", "unknown")
        queue = "unknown"
        if hasattr(request, "delivery_info") and request.delivery_info:
            queue = request.delivery_info.get("routing_key", "unknown")

        settings = get_settings()
        emit_task_lifecycle_metric(
            event="retried",
            task_name=task.name,
            queue=queue,
            retry_count=getattr(request, "retries", 0),
            outcome="retry",
            environment=getattr(settings, "env", "dev"),
        )
        logger.warning(
            "task_retried",
            extra={
                "event": "task_retried",
                "task_id": task_id,
                "task_name": task.name,
                "queue": queue,
                "retry_count": getattr(request, "retries", 0),
            },
        )

    @task_postrun.connect
    def on_task_postrun(task_id: str, **_: Any) -> None:
        _TASK_START_TIMES.pop(task_id, None)
        clear_request_context()
