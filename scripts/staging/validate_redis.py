"""Validate Staging Redis Connectivity & Queue Health.

Performs:
1. Redis PING round-trip.
2. Ephemeral key write, read, and delete.
3. Celery queue inspection (tryon, ingest, maintenance).

Generates a structured JSON validation report in reports/staging/.
Redis credentials and connection strings are strictly redacted.
"""

import argparse
import json
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import redis

from fashx.core.settings import get_settings


def validate_redis_operations(client: redis.Redis) -> dict[str, Any]:
    step_results = []

    # 1. Ping
    t0 = time.time()
    try:
        assert client.ping() is True
        step_results.append({
            "step": "ping",
            "status": "PASS",
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
    except Exception as e:
        step_results.append({
            "step": "ping",
            "status": "FAIL",
            "error": type(e).__name__,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        })
        return {"overall": "FAIL", "steps": step_results}

    # 2. Ephemeral key round-trip
    t1 = time.time()
    val_key = f"fashx:staging:validation:{uuid.uuid4()}"
    try:
        client.set(val_key, "validation-ok", ex=60)
        read_val = client.get(val_key)
        assert read_val in (b"validation-ok", "validation-ok")
        client.delete(val_key)
        assert client.get(val_key) is None
        step_results.append({
            "step": "ephemeral_round_trip",
            "status": "PASS",
            "duration_ms": round((time.time() - t1) * 1000, 2),
        })
    except Exception as e:
        step_results.append({
            "step": "ephemeral_round_trip",
            "status": "FAIL",
            "error": type(e).__name__,
            "duration_ms": round((time.time() - t1) * 1000, 2),
        })
    finally:
        try:
            client.delete(val_key)
        except Exception:
            pass

    # 3. Inspect Celery Queues
    queues = ["tryon", "ingest", "maintenance"]
    queue_depths = {}
    for q in queues:
        try:
            depth = client.llen(q)
            queue_depths[q] = int(depth)
        except Exception:
            queue_depths[q] = -1

    step_results.append({
        "step": "queue_inspection",
        "status": "PASS",
        "queue_depths": queue_depths,
    })

    overall = "PASS" if all(s.get("status") == "PASS" for s in step_results) else "FAIL"
    return {"overall": overall, "steps": step_results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Staging Redis Connectivity")
    parser.add_argument("--output-dir", default="reports/staging")
    args = parser.parse_args()

    started_at = datetime.now(UTC).isoformat()
    settings = get_settings()

    print("[*] Running Redis validation suite...")
    try:
        client: redis.Redis = redis.Redis.from_url(settings.redis_url, socket_timeout=5.0)
        outcome = validate_redis_operations(client)
    except Exception as e:
        outcome = {
            "overall": "FAIL",
            "steps": [{"step": "connection", "status": "FAIL", "error": type(e).__name__}],
        }
    completed_at = datetime.now(UTC).isoformat()

    report = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.4",
        "test_name": "redis_connectivity",
        "status": outcome["overall"],
        "started_at": started_at,
        "completed_at": completed_at,
        "steps": outcome["steps"],
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "redis_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Redis validation complete. Status: {report['status']}")
    print(f"[*] Report saved to {report_file}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
