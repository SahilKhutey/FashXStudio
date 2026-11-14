#!/usr/bin/env python3
"""FashXStudio — Celery Queue Topology and Routing Inspection Tool.

Inspects Celery task routing configurations, worker connectivity,
and Redis queue lengths across priority queues: 'tryon', 'ingest', and 'maintenance'.

Usage:
    python scripts/redis/test_celery_queues.py
"""

from __future__ import annotations

import sys
from typing import Any

from fashx.core.settings import get_settings
from fashx.workers.app import app


def inspect_routing_configuration() -> bool:
    print("--- 1. Inspecting Configured Task Routes ---")
    conf = app.conf
    task_routes = getattr(conf, "task_routes", {})
    expected_routes = {
        "fashx.workers.app.process_tryon_job": "tryon",
        "fashx.workers.app.ingest_catalog_feed": "ingest",
        "fashx.workers.app.enrich_garment_task": "ingest",
        "fashx.workers.app.relay_outbox_events": "maintenance",
        "fashx.workers.app.sweep_storage_erasure": "maintenance",
        "fashx.workers.app.run_retention_jobs": "maintenance",
    }

    all_ok = True
    for task_name, expected_queue in expected_routes.items():
        route = task_routes.get(task_name)
        actual_queue = route.get("queue") if isinstance(route, dict) else None
        if actual_queue == expected_queue:
            print(f"  [OK]  {task_name} -> queue '{actual_queue}'")
        else:
            print(f"  [MISMATCH] {task_name} -> expected '{expected_queue}', got '{actual_queue}'")
            all_ok = False

    return all_ok


def inspect_broker_and_queues(settings: Any) -> None:
    print("\n--- 2. Inspecting Redis Broker Queue Depths ---")
    print(f"Broker Target: {settings.redis_url}")

    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_timeout=2.0)
        client.ping()
        print("Broker Connection: [ESTABLISHED]")

        for queue_name in ["tryon", "ingest", "maintenance", "celery"]:
            try:
                length = client.llen(queue_name)
                print(f"  Queue '{queue_name}': {length} pending tasks")
            except Exception as e:
                print(f"  Queue '{queue_name}': query error ({e})")
        client.close()
    except Exception as exc:
        print(f"Broker Connection: [UNREACHABLE] ({exc})")
        print("Note: In environments where Redis is not active locally, this is expected.")


def inspect_celery_workers() -> None:
    print("\n--- 3. Inspecting Active Celery Workers ---")
    try:
        inspect = app.control.inspect(timeout=1.0)
        active_workers = inspect.ping()
        if active_workers:
            print(f"Active Worker Nodes ({len(active_workers)}):")
            for node, response in active_workers.items():
                print(f"  - Node: {node} ({response})")
        else:
            print("No active Celery workers discovered on broker.")
    except Exception as exc:
        print(f"Worker inspection skipped or unavailable: {exc}")


def main() -> None:
    settings = get_settings()
    print("==================================================================")
    print("FASHXSTUDIO CELERY QUEUE TOPOLOGY INSPECTOR")
    print(f"App Environment: {settings.app_env} (ENV={settings.env})")
    print("==================================================================")

    routing_ok = inspect_routing_configuration()
    inspect_broker_and_queues(settings)
    inspect_celery_workers()

    print("\n==================================================================")
    if routing_ok:
        print("RESULT: Task routing configuration verified successfully.")
    else:
        print("RESULT: Task routing configuration has discrepancies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
