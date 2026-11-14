"""Tests for Celery queue topology, routes, and broker reliability configuration."""

from __future__ import annotations

from fashx.workers.app import app
from fashx.workers.queue_config import (
    EXCHANGE,
    INGEST_QUEUE,
    MAINTENANCE_QUEUE,
    TASK_QUEUES,
    TASK_ROUTES,
    TRYON_QUEUE,
)


def test_exchange_configuration() -> None:
    assert EXCHANGE.name == "fashx"
    assert EXCHANGE.type == "direct"
    assert EXCHANGE.durable is True


def test_queue_definitions() -> None:
    queues_by_name = {q.name: q for q in TASK_QUEUES}

    assert "tryon" in queues_by_name
    assert "ingest" in queues_by_name
    assert "maintenance" in queues_by_name

    assert TRYON_QUEUE.routing_key == "tryon"
    assert TRYON_QUEUE.exchange.name == "fashx"
    assert TRYON_QUEUE.durable is True

    assert INGEST_QUEUE.routing_key == "ingest"
    assert INGEST_QUEUE.exchange.name == "fashx"
    assert INGEST_QUEUE.durable is True

    assert MAINTENANCE_QUEUE.routing_key == "maintenance"
    assert MAINTENANCE_QUEUE.exchange.name == "fashx"
    assert MAINTENANCE_QUEUE.durable is True


def test_task_routes_mapping() -> None:
    expected_routes = {
        "fashx.workers.app.process_tryon_job": "tryon",
        "fashx.workers.app.ingest_catalog_feed": "ingest",
        "fashx.workers.app.enrich_garment_task": "ingest",
        "fashx.workers.app.relay_outbox_events": "maintenance",
        "fashx.workers.app.sweep_storage_erasure": "maintenance",
        "fashx.workers.app.run_retention_jobs": "maintenance",
    }

    for task_name, queue_name in expected_routes.items():
        assert task_name in TASK_ROUTES, f"Missing route mapping for {task_name}"
        route = TASK_ROUTES[task_name]
        assert route.get("queue") == queue_name
        assert route.get("routing_key") == queue_name


def test_celery_broker_reliability_settings() -> None:
    conf = app.conf

    # Task execution reliability
    assert getattr(conf, "task_acks_late", False) is True
    assert getattr(conf, "task_reject_on_worker_lost", False) is True
    assert getattr(conf, "worker_prefetch_multiplier", None) == 1

    # Default queue fallback
    assert getattr(conf, "task_default_queue", None) == "maintenance"
    assert getattr(conf, "task_default_exchange", None) == "fashx"
    assert getattr(conf, "task_default_routing_key", None) == "maintenance"

    # Transport options: visibility timeout must exceed maximum task time limit (600s or 300s baseline)
    transport_opts = getattr(conf, "broker_transport_options", {})
    assert transport_opts.get("visibility_timeout", 0) >= 300
