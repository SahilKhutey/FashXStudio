# Structured Logging and Observability Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Reliability

---

## 1. Purpose and Foundation

This standard establishes uniform structured logging across FashXStudio backend services, background workers, and API endpoints. High-fidelity structured logging enables rapid incident diagnosis, performance tracing, and security auditing while strictly safeguarding user privacy and personal data.

Logging in FashXStudio builds directly on existing foundation modules:
- `backend/fashx/core/logging.py`: Structured JSON formatting and PII redaction filter.
- `backend/fashx/core/observability.py`: Sentry telemetry, OpenTelemetry context, and latency metrics.

No additional logging libraries or external dependencies may be introduced without formal architectural approval.

---

## 2. Standard Structured Fields

All log records produced in application and API contexts must output JSON formatted records containing the following canonical fields:

| Field | Type | Description | Example |
|---|---|---|---|
| `timestamp` | string (ISO 8601) | UTC timestamp of the log event | `"2026-11-11T09:45:00.123456Z"` |
| `level` | string | Standard logging severity level | `"INFO"`, `"WARNING"`, `"ERROR"` |
| `logger` | string | Python module logger name | `"fashx.vto.service"` |
| `message` | string | Human-readable description of the event | `"tryon_job_completed"` |
| `request_id` | string (UUID) | Unique request correlation identifier | `"e4c5d6a7-1234-4567-8901-123456789abc"` |
| `trace_id` | string (hex) | Distributed OpenTelemetry trace identifier | `"4bf92f3577b34da6a3ce929d0e0e4736"` |
| `method` | string | HTTP request method (where applicable) | `"POST"`, `"GET"` |
| `route_template` | string | Parameterized route path (not raw URL) | `"/api/v1/tryons/{job_id}"` |
| `status` | integer | HTTP status code (where applicable) | `200`, `422`, `503` |
| `latency_ms` | float | Execution duration in milliseconds | `428.5` |
| `error_code` | string (snake_case) | Stable application error code (if error) | `"tryon_provider_unavailable"` |
| `job_id` | string (UUID) | Background job identifier (where applicable)| `"a1b2c3d4-..."` |
| `app_version` | string | Running application version | `"0.1.0"` |

> **Unit Consistency Rule:** For execution timings, always use `latency_ms` (milliseconds). Never mix seconds and milliseconds or use unstructured string timings.

---

## 3. Logging Severity Levels

| Level | When to Use | Alerting / Action |
|---|---|---|
| `DEBUG` | Granular internal execution details, algorithm steps, and developer diagnostics in `dev` and `test`. | Suppressed in `prod`. |
| `INFO` | Normal lifecycle milestones (service startup, successful job completion, graceful shutdown). | Routine observability; no alerting. |
| `WARNING` | Degraded conditions, recoverable failures, rate-limit thresholds reached, retry attempts. | Monitored for trends; investigate if elevated. |
| `ERROR` | Unhandled exceptions, failed job processing, external integration outages, validation aborts. | Alerting triggered; requires engineer attention. |
| `CRITICAL` | Complete subsystem failure, database unreachable, data integrity risk, emergency shutdown. | Immediate on-call pager / high-severity incident. |

---

## 4. Code Examples

### Standard Operation Logging

```python
import logging

logger = logging.getLogger(__name__)

# Informational event with structured context
logger.info(
    "tryon_job_completed",
    extra={
        "job_id": str(job_id),
        "provider": provider_name,
        "latency_ms": elapsed_ms,
        "status": "completed",
    },
)
```

### Exception Logging

```python
try:
    await vto_client.submit_job(payload)
except ProviderTimeoutError as exc:
    logger.warning(
        "tryon_provider_timeout_retrying",
        extra={
            "job_id": str(job_id),
            "provider": "fashn",
            "attempt": retry_count,
            "latency_ms": elapsed_ms,
            "error_code": "tryon_timeout",
        },
        exc_info=False,  # Suppress full trace on known transient retries
    )
except Exception as exc:
    logger.error(
        "tryon_job_submission_failed",
        extra={
            "job_id": str(job_id),
            "error_code": "internal_error",
        },
        exc_info=True,  # Capture stack trace for unexpected errors
    )
```

---

## 5. Prohibited Sensitive Information (Zero-PII Policy)

In accordance with user privacy rules and data governance policies, the following ten categories of sensitive data **must NEVER appear in logs or telemetry**:

1. **Passwords and Hashes:** User passwords, password reset tokens, salt values.
2. **Authorization Headers & JWTs:** `Authorization: Bearer <token>`, refresh tokens, API keys, session secrets.
3. **Cloud & Third-Party Secrets:** AWS secret access keys, Fashn API keys, database connection strings.
4. **Presigned Storage URLs:** Temporary S3/GCS presigned download or upload URLs (which embed signature keys in query parameters).
5. **Raw Photographs & Binary Data:** Raw image bytes, base64 data URIs, or vector embedding arrays.
6. **Body Measurements:** User height, weight, waist, chest, or hip measurements.
7. **Skin Tone & Physical Attributes:** Biometric or physical attribute classifications.
8. **Contact Information:** Personal email addresses, phone numbers, or physical shipping addresses.
9. **Consent Payloads:** Detailed consent contract signatures containing user personal identifying information.
10. **Payment & Billing Data:** Credit card numbers, CVVs, bank account tokens, merchant payout secrets.

### Data Access Auditing

When recording audit events for user data access (e.g., GDPR/CCPA compliance), log only the metadata:
```json
{
  "event": "user_data_accessed",
  "actor_id": "usr_123",
  "target_user_id": "usr_123",
  "action": "export_profile",
  "status": "success"
}
```
Never log the contents of the exported profile or photos as evidence of the access event.

---

## 6. Context Correlation and Hygiene Rules

1. **Request Correlation:** Every HTTP request processed by FastAPI must generate or propagate a `request_id` via middleware and inject it into the logging context.
2. **Background Jobs:** Celery/Redis queue workers must preserve the originating `request_id` and `job_id` across task dispatch and execution.
3. **Redaction Filter:** All loggers must use `backend/fashx/core/logging.py`'s `RedactingFilter` to scrub inadvertent key leaks from free-text messages.
4. **No Full Payloads:** Do not log full HTTP request bodies or response payloads. Log validated identifiers and schema metadata only.
