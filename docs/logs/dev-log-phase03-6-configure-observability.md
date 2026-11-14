# Developer Log — Phase 03.6: Configure Observability

## 1. Engineering Scope and Goals

Phase 03.6 establishes an AWS-native, production-grade observability foundation for FashXStudio across the API gateway, background Celery workers, PostgreSQL database, Redis queues, Amazon S3 storage, and external Virtual Try-On (VTO) inference provider (FASHN API) in AWS Mumbai (`ap-south-1`).

The implementation addresses the requirements across the full Phase 03.6 scope:
1. Standardized structured JSON logging with centralized context (`service`, `environment`, `status_code`, `duration_ms`, `event`, `route`) and comprehensive PII/credential scrubbing (`backend/fashx/core/logging.py`).
2. CloudWatch Embedded Metric Format (EMF) operational metrics generator (`backend/fashx/core/metrics.py`) with strict runtime protection against high-cardinality dimension leakage.
3. Standards-compliant W3C `traceparent` distributed tracing (`backend/fashx/core/tracing.py`) propagating trace context from HTTP gateway to Celery workers via Redis.
4. Error tracking and exception monitoring via Sentry SDK (`backend/fashx/core/observability.py`) with deep recursive `before_send` PII and token scrubbing.
5. Inbound HTTP gateway middleware instrumentation (`backend/fashx/gateway/middleware.py`) with request ID validation (`^[A-Za-z0-9._-]{1,64}$`), latency tracking, and context cleanup guarantees.
6. Database connection pool telemetry (`backend/fashx/core/database.py`) monitoring SQLAlchemy pool checkouts, overflows, and health check latency.
7. Celery worker telemetry and lifecycle signals (`backend/fashx/workers/telemetry.py`, `backend/fashx/workers/signals.py`) measuring task duration, retries, dead letters, worker heartbeats, and queue depth.
8. Amazon S3 storage adapter telemetry (`backend/fashx/infrastructure/storage/s3.py`) measuring bytes uploaded, operation latencies, and erasure failures.
9. VTO provider adapter telemetry (`backend/fashx/infrastructure/tryon/fashn_api.py`) tracking inference latency, 429 rate limits, 401 auth failures, and per-render spend estimates.
10. CloudWatch declarative infrastructure definitions:
    - Unified operations dashboard (`infra/aws/observability/cloudwatch/dashboard.json`).
    - 12 CloudWatch alarms across API, RDS, Redis, Celery, S3, and VTO (`infra/aws/observability/cloudwatch/alarms.yaml`).
    - 15 CloudWatch log groups with retention rules (`infra/aws/observability/cloudwatch/log-groups.yaml`).
    - 3 SNS notification topics (`infra/aws/observability/cloudwatch/sns-topics.yaml`).
    - Least-privilege IAM task policy for telemetry (`infra/aws/observability/iam/observability-task-policy.json`).
    - AWS Budgets configurations with alert thresholds (`infra/aws/observability/budgets/budgets.yaml`).

## 2. Key Architecture Decisions

- **Daemonless Metric Generation via CloudWatch EMF**: By using CloudWatch Embedded Metric Format printed synchronously to stdout, the application achieves high-resolution operational metrics without running an auxiliary metrics daemon, Prometheus scraper, or StatsD agent on ECS Fargate.
- **Strict High-Cardinality Dimension Blacklist**: Custom metric billing can escalate dramatically if high-cardinality values are placed into metric dimensions. The `emit_metric()` function enforces a strict runtime guard that forbids `request_id`, `user_id`, `job_id`, raw URLs, and object keys from dimensions, restricting dimensions to fixed sets (`Environment`, `Route`, `Method`, `StatusCode`, `Queue`, `Category`, `Stage`).
- **ContextVar Cleanup in Early Returns & Failures**: Request context is set as early as possible in `RequestCorrelationMiddleware`, but is rigorously cleared in `finally` blocks, including early HTTP 503 maintenance mode returns and unhandled exception paths, ensuring zero leakage across concurrent async coroutines.
- **Cross-Service W3C Traceparent Propagation**: Tasks dispatched via `apply_async` carry `request_id`, `trace_id`, and `traceparent` headers in message metadata. Celery workers extract these headers in `task_prerun` signal hooks, continuing the exact distributed trace initiated by the mobile client or API consumer.
- **Deep Sentry Redaction**: Sentry `before_send` and `before_breadcrumb` processors traverse nested dictionaries and scrub sensitive authentication credentials, Bearer tokens, and AWS S3 presigned signatures using recursive key matching and regex scrubbers.

## 3. Environment Disclosures (AGENTS.md Rule 14)

- AWS CloudWatch dashboards, alarms, log groups, SNS topics, and AWS Budgets are authored as declarative YAML/JSON infrastructure specifications in `infra/aws/observability/`. They require live deployment to AWS by the human founder with active AWS account access.
- Local verification was executed against the project's local test suites (`tests/observability/`), linting tools, and documentation checks.
