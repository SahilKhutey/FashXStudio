# API Operational Metrics Specification

## 1. Overview

FashXStudio instruments all inbound HTTP requests at the gateway layer using standard FastAPI middleware (`backend/fashx/gateway/middleware.py`). Metrics are formatted in AWS CloudWatch Embedded Metric Format (EMF) and emitted synchronously to stdout via `backend/fashx/core/metrics.py`.

CloudWatch automatically extracts these metrics into the CloudWatch namespace `FashX/API` without requiring a separate telemetry sidecar or metrics collector daemon.

## 2. Emitted Metrics

| Metric Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `ApiRequestsCount` | Counter | Count | Total count of HTTP requests processed by the API gateway. |
| `ApiLatency` | Timer | Milliseconds | End-to-end request latency measured from middleware entry to response exit. |
| `Api5xxErrors` | Counter | Count | Total count of 5xx server-side error responses returned. |
| `Api4xxErrors` | Counter | Count | Total count of 4xx client-side error responses returned. |
| `HealthCheckStatus` | Gauge | Count | Status of `/healthz/live` (1 = Healthy, 0 = Unhealthy). |
| `ReadinessCheckStatus` | Gauge | Count | Status of `/healthz/ready` (1 = Ready, 0 = Dependency Unhealthy). |

## 3. Metric Dimensions & Cardinality Guardrails

To protect against uncontrolled AWS CloudWatch custom metric billing, dimensions are strictly constrained to low-cardinality values.

### Allowed Dimensions
- `Environment`: `dev`, `staging`, `prod`
- `Route`: Low-cardinality route template (e.g. `/api/v1/tryon/{job_id}`, `/api/v1/catalog/products`)
- `Method`: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`
- `StatusCode`: HTTP response status code (e.g. `200`, `400`, `404`, `500`)

### Prohibited Dimensions
The `emit_metric` utility in `backend/fashx/core/metrics.py` enforces a runtime guard against prohibited high-cardinality keys:
- `request_id`, `trace_id`, `traceparent`
- `user_id`, `merchant_id`, `session_id`
- `job_id`, `product_id`, `media_id`
- Raw URLs containing dynamic query strings or path parameters

Dynamic path resolution replaces path arguments with route templates extracted from `request.scope.get("endpoint")` or `request.url.path` normalization.

## 4. Latency SLA & Objectives

| Endpoint Category | Target p50 | Target p95 | Target p99 | Max Acceptable |
| :--- | :--- | :--- | :--- | :--- |
| **Health Checks** (`/healthz/*`) | < 5 ms | < 15 ms | < 30 ms | 100 ms |
| **Catalog & Feed Retrieval** | < 40 ms | < 150 ms | < 300 ms | 500 ms |
| **VTO Job Submission** | < 50 ms | < 200 ms | < 400 ms | 1000 ms |
| **Media Metadata / Upload Prep** | < 30 ms | < 100 ms | < 250 ms | 500 ms |

## 5. Health & Readiness Telemetry

Health endpoints are instrumented to record dependency health:
- `/healthz/live`: Validates event loop and basic runtime execution. Emits `HealthCheckStatus=1`.
- `/healthz/ready`: Validates live connectivity to PostgreSQL (`SELECT 1`) and Redis (`PING`). Emits `ReadinessCheckStatus=1` if all pass; `ReadinessCheckStatus=0` and 503 if any core dependency fails.

## 6. Verification & Automated Testing

API telemetry is verified by tests in:
- `tests/observability/test_metrics.py`: Confirms EMF serialization, JSON structure, and dimension filtering.
- `tests/observability/test_request_context.py`: Asserts metrics and latency are logged and emitted upon request completion, even during maintenance mode or error scenarios.
