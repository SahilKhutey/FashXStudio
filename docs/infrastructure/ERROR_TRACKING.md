# Error Tracking Specification — Sentry Integration

## 1. Overview

FashXStudio integrates Sentry for application error tracking, unhandled exception aggregation, and release health monitoring across all environments (`dev`, `staging`, `prod`).

The integration is implemented in `backend/fashx/core/observability.py` and initialized at service startup in both the FastAPI gateway (`backend/fashx/main.py`) and background worker entrypoints (`backend/fashx/workers/app.py`).

## 2. Configuration & Initialization

Sentry initialization adheres strictly to dependency injection and configuration standards:
- The configuration function `configure_sentry(settings)` accepts the application settings object directly.
- The Sentry DSN is retrieved from `settings.sentry_dsn` (populated via AWS Secrets Manager or environment variables).
- If `sentry_dsn` is omitted, blank, or set to placeholder values, Sentry initializes as disabled (no-op) without throwing errors.
- Environments are mapped explicitly: `dev`, `staging`, `prod`.
- Releases are tagged with `settings.app_version` (e.g., `0.3.6`).

```python
from fashx.core.config import get_settings
from fashx.core.observability import configure_sentry

settings = get_settings()
configure_sentry(settings)
```

## 3. Privacy, PII, and Credential Sanitization

In compliance with FashX security guidelines and privacy mandates, raw user credentials, authentication tokens, and presigned media URLs must never reach external error aggregation platforms.

### 3.1 `before_send` Event Scrubbing

Every Sentry event passes through `_sentry_before_send(event, hint)` prior to transmission:
1. **Request Body Sanitization**: Recursively traverses dictionary payloads and replaces values for sensitive keys (`password`, `token`, `authorization`, `secret`, `api_key`, `access_token`, `refresh_token`, `client_secret`, `session_token`, `private_key`) with `[redacted]`.
2. **Regex URL and Token Scrubbing**: Applies regex filters against URLs, query strings, and exception messages to scrub:
   - AWS S3 presigned signature parameters (`X-Amz-Signature=...`).
   - Bearer tokens in headers (`Bearer eyJ...`).
   - Generic API tokens.
3. **User Identity Masking**: The `user` context is scrubbed of all PII. Only an opaque, non-identifying hash or system ID is retained if configured; raw phone numbers, email addresses, and names are stripped.

### 3.2 Breadcrumb Sanitization

Breadcrumbs recorded during request execution pass through `_sentry_before_breadcrumb(crumb, hint)`:
- HTTP client breadcrumbs strip query strings from external HTTP calls (preventing token leakage to upstream APIs like FASHN).
- Database query breadcrumbs sanitize literal values.
- Log message breadcrumbs run through standard redaction.

## 4. Error Classification and Tagging

All captured exceptions are tagged with standardized operational dimensions to enable rapid filtering in the Sentry UI:
- `service`: `api` or `worker`
- `environment`: `dev`, `staging`, `prod`
- `release`: Version string (e.g. `0.3.6`)
- `route`: Matched route template (e.g. `/api/v1/tryon/{job_id}`)
- `request_id`: Tracing correlation ID (`X-Request-ID`)
- `trace_id`: Distributed W3C trace ID

### Exception Severity Hierarchy
| Level | Criteria | Example |
| :--- | :--- | :--- |
| **FATAL** | Service cannot start or catastrophic failure | Database connection failure at boot |
| **ERROR** | Unhandled 500 error or Celery job dead-lettered | Unexpected API crash, unhandled provider failure |
| **WARNING** | Handled business logic failure or transient retry | FASHN API 429 rate limit (retry scheduled), DB reconnect |
| **INFO** | Informational operational milestone | Deployment marker, migration completion |

## 5. Verification & Testing

Sentry integration is verified via unit tests in `tests/observability/test_sentry_config.py`:
- `test_configure_sentry_disabled_when_empty_dsn`: Asserts graceful handling when no DSN is provided.
- `test_sentry_before_send_redacts_credentials`: Verifies recursive stripping of passwords, bearer tokens, and presigned S3 URLs from Sentry event payloads.
