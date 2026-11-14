"""Validate Staging Log Formatting, Request Correlation, and Redaction.

Performs:
1. Structured JSON schema verification.
2. Request ID correlation validation.
3. Sensitive data redaction verification.

Generates a structured JSON validation report in reports/staging/.
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fashx.core.logging import JsonFormatter, RedactFilter, scrub
from fashx.core.tracing import generate_traceparent, parse_traceparent


def validate_logging_subsystem() -> dict[str, Any]:
    step_results = []

    # 1. JSON formatting
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="fashx.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=25,
        msg="validation_log_message",
        args=(),
        exc_info=None,
    )
    record.request_id = "staging-req-001"
    record.trace_id = "trace-staging-001"
    record.route = "/api/v1/healthz/live"
    record.status_code = 200
    record.duration_ms = 12.5

    try:
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        assert parsed["level"] == "INFO"
        assert parsed["request_id"] == "staging-req-001"
        assert parsed["route"] == "/api/v1/healthz/live"
        step_results.append({
            "step": "json_schema_validation",
            "status": "PASS",
            "sample_keys": list(parsed.keys()),
        })
    except Exception as e:
        step_results.append({
            "step": "json_schema_validation",
            "status": "FAIL",
            "error": type(e).__name__,
        })

    # 2. Redaction filter
    redact_filter = RedactFilter()
    sensitive_record = logging.LogRecord(
        name="fashx.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=50,
        msg="Failed auth with X-Amz-Signature=abcdef1234567890 and user email test.user@example.com",
        args=(),
        exc_info=None,
    )
    redact_filter.filter(sensitive_record)
    try:
        assert "abcdef1234567890" not in sensitive_record.msg
        assert "test.user@example.com" not in sensitive_record.msg
        assert "[redacted]" in sensitive_record.msg

        # Dict scrubbing
        raw_dict = {"api_key": "top-secret-key", "password": "super-password", "safe": "public"}
        scrubbed = scrub(raw_dict)
        assert scrubbed["api_key"] == "[redacted]"
        assert scrubbed["password"] == "[redacted]"
        assert scrubbed["safe"] == "public"

        step_results.append({
            "step": "sensitive_data_redaction",
            "status": "PASS",
        })
    except Exception as e:
        step_results.append({
            "step": "sensitive_data_redaction",
            "status": "FAIL",
            "error": type(e).__name__,
        })

    # 3. W3C Traceparent
    try:
        traceparent_header = generate_traceparent(sampled=True)
        parsed = parse_traceparent(traceparent_header)
        assert parsed is not None
        trace_id, parent_id, flags = parsed
        assert len(trace_id) == 32
        assert len(parent_id) == 16
        step_results.append({
            "step": "traceparent_propagation",
            "status": "PASS",
        })
    except Exception as e:
        step_results.append({
            "step": "traceparent_propagation",
            "status": "FAIL",
            "error": type(e).__name__,
        })

    overall = "PASS" if all(s.get("status") == "PASS" for s in step_results) else "FAIL"
    return {"overall": overall, "steps": step_results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Log Formatting and Correlation")
    parser.add_argument("--output-dir", default="reports/staging")
    args = parser.parse_args()

    started_at = datetime.now(UTC).isoformat()
    print("[*] Validating logging, correlation, and redaction...")
    outcome = validate_logging_subsystem()
    completed_at = datetime.now(UTC).isoformat()

    report = {
        "phase": "03.7",
        "environment": "staging",
        "test_id": "3.7.8",
        "test_name": "log_validation",
        "status": outcome["overall"],
        "started_at": started_at,
        "completed_at": completed_at,
        "steps": outcome["steps"],
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "log_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Log validation complete. Status: {report['status']}")
    print(f"[*] Report saved to {report_file}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
