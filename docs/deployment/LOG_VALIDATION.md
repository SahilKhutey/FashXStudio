# Log Formatting, Correlation & Redaction Validation

## 1. Overview

Logging validation proves that the API gateway, background workers, and migration tasks emit structured, queryable, and privacy-safe logs to Amazon CloudWatch Logs under the `/ecs/fashx/staging` log group.

Verification is executed via `scripts/staging/validate_logs.py`.

## 2. Standard JSON Log Schema

All services emit single-line JSON records adhering to the standard schema:

```json
{
  "timestamp": "2026-11-14T05:22:11.731619+00:00",
  "level": "INFO",
  "service": "api",
  "environment": "staging",
  "app_version": "0.3.7",
  "logger": "fashx.gateway.middleware",
  "event": "http_request",
  "message": "http_request",
  "request_id": "req-948194",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "route": "/api/v1/feed",
  "status_code": 200,
  "duration_ms": 34.2
}
```

## 3. Request Correlation & Distributed Tracing

1. **`X-Request-ID`**: Validated against `^[A-Za-z0-9._-]{1,64}$`. Conforming request IDs are propagated to downstream logs, error reports, and HTTP response headers. Malformed IDs are replaced with generated UUID4 strings.
2. **W3C `traceparent`**: Follows W3C Trace Context specifications (`00-<32hex>-<16hex>-<flags>`). Injected into Celery message headers during `apply_async` and extracted in worker `task_prerun` hooks.

## 4. Credential & PII Redaction Controls

To prevent sensitive data leakage into CloudWatch Logs:
- **Key Blacklist**: 21 sensitive keys (`password`, `token`, `secret`, `api_key`, `authorization`, `private_key`, etc.) are automatically scrubbed to `[redacted]` in dictionaries and JSON payloads.
- **Regex Scrubbing**: Text streams are scrubbed for:
  - Bearer tokens and JWTs (`eyJ...`).
  - S3 Presigned Signatures (`X-Amz-Signature=...`).
  - Passwords in connection URLs (`postgresql://user:pass@host/db`).
  - Email addresses (`user@domain.com`).
  - Base64 image payload strings (`data:image/...`).

## 5. Execution Commands

```bash
# Execute log validation
python scripts/staging/validate_logs.py --output-dir reports/staging
```

### Expected Output
```text
[*] Validating logging, correlation, and redaction...
[*] Log validation complete. Status: PASS
[*] Report saved to reports/staging/log_report.json
```

## 6. Acceptance Criteria

- CloudWatch Logs contains parseable JSON entries with UTC timestamps.
- Request ID and trace ID fields correlate API requests to worker task execution.
- Automated tests confirm that sensitive keys, passwords, and tokens are scrubbed.
