import pytest

from backend.fashx.workers.validation_tasks import (
    staging_fatal_task,
    staging_ingest_ping,
    staging_maintenance_ping,
    staging_retryable_task,
    staging_tryon_ping,
    staging_worker_ping,
)


def test_staging_worker_ping_direct():
    result = staging_worker_ping()
    assert result["status"] == "ok"
    assert "completed_at" in result


def test_queue_specific_pings():
    res_tryon = staging_tryon_ping()
    assert res_tryon["status"] == "ok"
    assert res_tryon["queue"] == "tryon"

    res_ingest = staging_ingest_ping()
    assert res_ingest["status"] == "ok"
    assert res_ingest["queue"] == "ingest"

    res_maint = staging_maintenance_ping()
    assert res_maint["status"] == "ok"
    assert res_maint["queue"] == "maintenance"


def test_staging_retryable_task_success():
    res = staging_retryable_task(fail_count=0)
    assert res["status"] == "succeeded_after_retry"
    assert res["attempts"] == 1


def test_staging_fatal_task_raises():
    with pytest.raises(ValueError, match="Controlled diagnostic fatal failure"):
        staging_fatal_task()
