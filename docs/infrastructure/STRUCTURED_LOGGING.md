# Structured Logging Specification

## 1. Standard Log Schema

All backend processes (FastAPI, Celery workers, migration tasks, and Beat scheduler) emit structured JSON formatted records to standard output (`stdout`), captured by the AWS CloudWatch log driver.

### Canonical Schema Example
```json
{
  "timestamp": "2026-11-14T04:40:00.000Z",
  "level": "INFO",
  "service": "fashx-api",
  "environment": "staging",
  "app_version": "0.2.0",
  "logger": "fashx.gateway.middleware",
  "event": "http_request",
  "request_id": "f5b2d9a1-7c3e-4b21-8f92-123456789abc",
  "trace_id": "a6c4d8e20f1b2c3d4e5f6a7b8c9d0e1f",
  "method": "GET",
  "route": "/api/v1/feed",
  "status_code": 200,
  "duration_ms": 142.7,
  "error_code": null,
  "message": "http_request"
}
```

## 2. Field Definitions

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | String (ISO-8601 UTC) | Precise UTC timestamp of the log event. |
| `level` | String | Standard logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `service` | String | Logical originating subsystem: `api`, `tryon`, `ingest`, `beat`, `migration`. |
| `environment` | String | Target deployment environment: `dev`, `staging`, `prod`. |
| `app_version` | String | Current immutable application version. |
| `logger` | String | Python logger module name (e.g. `fashx.gateway.middleware`). |
| `event` | String | Stable event identifier (e.g. `http_request`, `task_started`, `personal_data_access`). |
| `request_id` | String | Request correlation identifier (`X-Request-ID`). |
| `trace_id` | String | Distributed 32-character hex trace identifier. |
| `method` | String | HTTP verb (`GET`, `POST`, etc.) for web requests. |
| `route` | String | Matched route template (e.g. `/api/v1/feed`), avoiding raw URL query parameters. |
| `status_code`| Integer | HTTP response status code or terminal task exit code. |
| `duration_ms` | Float | Measured execution latency in milliseconds. |
| `error_code` | String / Null | Internal stable error classification code if an error occurred. |
| `job_id` | String / Null | Internal asynchronous UUID for background job correlation. |

## 3. Redaction and Privacy Policy

The logging pipeline applies a mandatory `RedactFilter` on the root logger. The filter scrubs sensitive data before JSON serialization:
- **Sensitive Keys**: `authorization`, `token`, `password`, `secret`, `api_key`, `bearer`, `cookie`, `set-cookie`, `database_url`, `redis_url`, `access_key`, `secret_access_key`, `fashn_api_key`, `signed_url`, `presigned_url`, `image_bytes`, `photo`, `body_measurements`, `skin_tone`, `email`, `phone`.
- **Pattern Matching**: Regex scrubbing of JWT tokens, presigned S3 query parameters, email addresses, base64 strings, and connection strings containing passwords.
- **Rule of Least Privilege**: Sensitive user payloads, base64 images, and raw merchant CSV data must never be passed to log arguments.
