"""Validate Staging API Deployment Health.

Tests public health endpoints:
- /healthz/live
- /healthz/ready
- /api/v1/system/health/live (fallback)
- /api/v1/system/health/ready (fallback)

Generates a structured JSON validation report in reports/staging/.
"""

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_endpoint(base_url: str, path: str, timeout: int = 10) -> dict[str, str | int]:
    url = f"{base_url.rstrip('/')}{path}"
    req = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "FashX-Deployment-Validator/1.0"},
        method="GET",
    )
    start_time = time.time()
    try:
        with urlopen(req, timeout=timeout) as response:
            status = int(response.status)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "endpoint": path,
                "status_code": status,
                "result": "PASS" if status == 200 else "FAIL",
                "duration_ms": duration_ms,
            }
    except HTTPError as err:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "endpoint": path,
            "status_code": int(err.code),
            "result": "FAIL",
            "error": f"HTTPError: {err.reason}",
            "duration_ms": duration_ms,
        }
    except URLError as err:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "endpoint": path,
            "status_code": 0,
            "result": "FAIL",
            "error": f"URLError: {err.reason}",
            "duration_ms": duration_ms,
        }
    except Exception as err:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "endpoint": path,
            "status_code": 0,
            "result": "FAIL",
            "error": f"Unexpected: {type(err).__name__}",
            "duration_ms": duration_ms,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Staging Deployment Health")
    parser.add_argument("--base-url", default=os.getenv("STAGING_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--output-dir", default="reports/staging")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"[*] Validating deployment health against {base_url}...")

    endpoints = [
        "/healthz/live",
        "/healthz/ready",
        "/api/v1/system/health/live",
        "/api/v1/system/health/ready",
    ]

    started_at = datetime.now(UTC).isoformat()
    results = [check_endpoint(base_url, ep) for ep in endpoints]
    completed_at = datetime.now(UTC).isoformat()

    passed_count = sum(1 for r in results if r.get("result") == "PASS")
    failed_count = len(results) - passed_count

    report = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.2",
        "test_name": "health_endpoints",
        "status": "PASS" if failed_count == 0 else "FAIL",
        "target_url": base_url,
        "started_at": started_at,
        "completed_at": completed_at,
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "failed": failed_count,
        },
        "results": results,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "deployment_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Health validation complete. Result: {report['status']} (Passed: {passed_count}/{len(results)})")
    print(f"[*] Report saved to {report_file}")
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
