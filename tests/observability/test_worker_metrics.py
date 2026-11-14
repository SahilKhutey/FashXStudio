from fashx.workers.telemetry import (
    emit_queue_depth,
    emit_task_lifecycle_metric,
    emit_worker_heartbeat,
)


def test_emit_worker_heartbeat():
    event = emit_worker_heartbeat("tryon", environment="staging")
    assert event["Service"] == "worker-tryon"
    assert event["Environment"] == "staging"
    assert event["WorkerType"] == "tryon"
    assert event["WorkerHeartbeat"] == 1.0
    assert event["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "FashX/Workers"


def test_emit_queue_depth():
    event = emit_queue_depth("ingest", depth=14, environment="prod")
    assert event["Service"] == "worker"
    assert event["Environment"] == "prod"
    assert event["Queue"] == "ingest"
    assert event["QueueDepth"] == 14.0
    assert event["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "FashX/Queues"


def test_task_lifecycle_metrics_emission(monkeypatch):
    emitted = []

    def mock_emit_metric(name, value, unit, **kwargs):
        emitted.append((name, value, unit, kwargs))
        return {}

    monkeypatch.setattr("fashx.workers.telemetry.emit_metric", mock_emit_metric)

    # 1. Started
    emit_task_lifecycle_metric(
        event="started",
        task_name="fashx.workers.app.process_tryon_job",
        queue="tryon",
        environment="staging",
    )
    assert any(m[0] == "TaskStarted" for m in emitted)

    # 2. Succeeded with duration
    emitted.clear()
    emit_task_lifecycle_metric(
        event="succeeded",
        task_name="fashx.workers.app.process_tryon_job",
        queue="tryon",
        duration_ms=450.0,
        environment="staging",
    )
    assert any(m[0] == "TaskSucceeded" for m in emitted)
    assert any(m[0] == "TaskDuration" and m[1] == 450.0 for m in emitted)

    # 3. Failed
    emitted.clear()
    emit_task_lifecycle_metric(
        event="failed",
        task_name="fashx.workers.app.ingest_catalog_feed",
        queue="ingest",
        duration_ms=210.0,
        outcome="failure",
        environment="staging",
    )
    assert any(m[0] == "TaskFailed" for m in emitted)
    assert any(m[0] == "TaskDuration" for m in emitted)

    # 4. Retried
    emitted.clear()
    emit_task_lifecycle_metric(
        event="retried",
        task_name="fashx.workers.app.process_tryon_job",
        queue="tryon",
        retry_count=2,
        environment="staging",
    )
    assert any(m[0] == "TaskRetried" for m in emitted)

    # 5. Dead-Lettered
    emitted.clear()
    emit_task_lifecycle_metric(
        event="dead_lettered",
        task_name="fashx.workers.app.process_tryon_job",
        queue="tryon",
        environment="staging",
    )
    assert any(m[0] == "TaskDeadLettered" for m in emitted)
