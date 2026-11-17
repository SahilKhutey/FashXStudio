"""Infrastructure tests for Redis caching configuration and Celery task queues.

Validates that connection pool parameters, task routing maps, prefetch policies,
and worker persistence invariants comply with architectural specifications.
"""

from __future__ import annotations

from fashx.core.settings import Settings
from fashx.workers.app import app


def test_settings_redis_pool_parameters() -> None:
    settings = Settings(
        env="dev",
        app_env="development",
        redis_url="redis://localhost:6379/0",
        redis_max_connections=35,
        redis_socket_timeout=8.0,
        redis_socket_connect_timeout=4.0,
        redis_ssl_cert_reqs="required",
    )
    assert settings.redis_max_connections == 35
    assert settings.redis_socket_timeout == 8.0
    assert settings.redis_socket_connect_timeout == 4.0
    assert settings.redis_ssl_cert_reqs == "required"


def test_celery_task_routes_mapping() -> None:
    conf = app.conf
    routes = getattr(conf, "task_routes", {})

    expected = {
        "fashx.workers.app.process_tryon_job": "tryon",
        "fashx.workers.app.ingest_catalog_feed": "ingest",
        "fashx.workers.app.enrich_garment_task": "ingest",
        "fashx.workers.app.relay_outbox_events": "maintenance",
        "fashx.workers.app.sweep_storage_erasure": "maintenance",
        "fashx.workers.app.run_retention_jobs": "maintenance",
    }

    for task_name, queue_name in expected.items():
        assert task_name in routes, f"Task {task_name} missing from Celery task_routes"
        route_config = routes[task_name]
        assert isinstance(route_config, dict)
        assert route_config.get("queue") == queue_name, (
            f"Expected {task_name} -> queue {queue_name}, got {route_config.get('queue')}"
        )


def test_celery_worker_reliability_policies() -> None:
    conf = app.conf
    # Worker prefetch multiplier should be 1 to prevent worker starvation on long VTO tasks
    assert getattr(conf, "worker_prefetch_multiplier", None) == 1
    # Tasks should acknowledge late (after successful execution)
    assert getattr(conf, "task_acks_late", None) is True
    # Tasks should be rejected and requeued if worker process crashes
    assert getattr(conf, "task_reject_on_worker_lost", None) is True
    # Task results should expire after 3600 seconds
    assert getattr(conf, "result_expires", None) == 3600
