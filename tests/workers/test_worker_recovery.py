"""Tests for Celery worker lifecycle, task timeouts, retry policies, and graceful shutdown."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from fashx.workers.app import (
    app,
    enrich_garment_task,
    ingest_catalog_feed,
    process_tryon_job,
    relay_outbox_events,
    run_retention_jobs,
    sweep_storage_erasure,
)


def test_task_timeout_configurations() -> None:
    expected_timeouts = {
        process_tryon_job: (105, 115),
        ingest_catalog_feed: (480, 600),
        enrich_garment_task: (240, 300),
        relay_outbox_events: (45, 60),
        sweep_storage_erasure: (120, 150),
        run_retention_jobs: (480, 600),
    }

    for task_obj, (expected_soft, expected_hard) in expected_timeouts.items():
        assert getattr(task_obj, "soft_time_limit", None) == expected_soft, (
            f"{task_obj.name} soft_time_limit expected {expected_soft}, got {getattr(task_obj, 'soft_time_limit', None)}"
        )
        assert getattr(task_obj, "time_limit", None) == expected_hard, (
            f"{task_obj.name} time_limit expected {expected_hard}, got {getattr(task_obj, 'time_limit', None)}"
        )


def test_task_max_retries_configurations() -> None:
    expected_retries = {
        process_tryon_job: 3,
        ingest_catalog_feed: 3,
        enrich_garment_task: 2,
        relay_outbox_events: 5,
        sweep_storage_erasure: 3,
        run_retention_jobs: 2,
    }

    for task_obj, expected_max in expected_retries.items():
        assert getattr(task_obj, "max_retries", None) == expected_max, (
            f"{task_obj.name} max_retries expected {expected_max}, got {getattr(task_obj, 'max_retries', None)}"
        )


def test_worker_graceful_shutdown_configuration() -> None:
    conf = app.conf
    assert getattr(conf, "worker_soft_shutdown_timeout", None) == 90.0
    assert getattr(conf, "worker_enable_soft_shutdown_on_idle", None) is True
    assert (
        getattr(conf, "worker_cancel_long_running_tasks_on_connection_loss", None)
        is True
    )


def test_fashx_task_on_failure_triggers_dead_letter_persistence() -> None:
    task_instance = process_tryon_job
    fake_job_id = str(uuid4())

    with patch("fashx.workers.app.persist_dead_letter_sync") as mock_persist:
        # Simulate on_failure callback invoked by Celery harness
        task_instance.on_failure(
            exc=TimeoutError("VTO inference timed out"),
            task_id="test-task-uuid",
            args=(fake_job_id,),
            kwargs={},
            einfo=None,
        )

        assert mock_persist.called
        call_kwargs = mock_persist.call_args[1]
        assert call_kwargs["task_id"] == "test-task-uuid"
        assert call_kwargs["task_name"] == "fashx.workers.app.process_tryon_job"
        assert call_kwargs["error_type"] == "TimeoutError"
        assert "VTO inference timed out" in call_kwargs["error_message"]
        assert call_kwargs["safe_payload"] == {"job_id": fake_job_id}


def test_process_tryon_job_refuses_retry_on_non_retryable_value_error() -> None:
    with patch.object(process_tryon_job, "retry") as mock_retry:
        with pytest.raises(ValueError):
            # Pass invalid UUID string which raises ValueError
            process_tryon_job.run("invalid-not-a-uuid")

        # Retry must NOT be invoked on ValueError
        assert not mock_retry.called
