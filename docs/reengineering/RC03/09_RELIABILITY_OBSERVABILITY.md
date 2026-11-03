# RC-03 — Reliability & Observability

## Health Probes
The backend exposes standardized Kubernetes/container-ready health probes:

- **Liveness Probe**:
  - `/healthz/live` & `/api/v1/system/health/live`
  - Returns `{"status": "ok", "service": "...", "version": "...", "timestamp": "..."}`
- **Readiness Probe**:
  - `/healthz/ready` & `/api/v1/system/health/ready`
  - Evaluates database connectivity, redis dependency, and auth JWKS configuration.
  - Returns HTTP 200 when ready, HTTP 503 with dependency status map when degraded.

## Mobile Client Network Resilience
In `mobile/src/app-shell/queryClient.ts`, network retries are configured using `ApiError.isRetryable(error)`:
- Idempotent GET requests retry up to 2 times with exponential backoff on network failures or HTTP 503/504 errors.
- Client errors (HTTP 400, 401, 403, 404, 422) do not retry, avoiding redundant server load.

## Structured Logging & Tracing
All incoming HTTP requests pass through gateway middleware assigning unique `request_id` and `trace_id` headers, emitted in JSON-formatted log lines across all subsystem use cases.
