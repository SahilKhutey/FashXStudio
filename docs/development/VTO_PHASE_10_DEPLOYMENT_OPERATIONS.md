# FashXStudio — VTO Phase 10: Deployment & Operational Readiness

**Status:** Implementation specification  
**Phase:** VTO 10 of 12  
**Target Environment:** AWS Mumbai (`ap-south-1`)  
**Deployment Model:** ECS Fargate, RDS PostgreSQL, ElastiCache Redis, private S3  
**Prerequisite:** VTO Phase 9 — AI Quality Evaluation, Visual Accuracy & Feedback Learning  

---

## 1. Objective

Deploy the complete Virtual Try-On (VTO) workflow as independently scalable API and background-worker services. Ensure secure image handling, reliable job processing, observability, fault recovery, and controlled deployment releases.

The production runtime encompasses:
$$\text{Mobile App} \longrightarrow \text{HTTPS/ALB} \longrightarrow \text{FastAPI (ECS)} \longrightarrow \text{Redis Queue} \longrightarrow \text{Try-On Worker (ECS)} \longrightarrow \text{Fashn API} \longrightarrow \text{Private S3}$$

---

## 2. Deployment Services & Topology

### 2.1 Service Breakdown
| Service | Runtime Container | Process Command | Responsibility |
|---|---|---|---|
| **`fashx-api`** | ECS Fargate | `gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 --timeout 90 --graceful-timeout 30 --forwarded-allow-ips "*" fashx.main:app` | Authenticated client API, job submission, wardrobe, status |
| **`fashx-worker`** | ECS Fargate | `celery -A fashx.workers.app:app worker --loglevel=INFO --queues=tryon --concurrency=3 --hostname=tryon@%h` | Consumes `tryon` queue, executes provider inference, stores artifacts |
| **`fashx-ingest`** | ECS Fargate | `celery -A fashx.workers.app:app worker --loglevel=INFO --queues=ingest --concurrency=2 --hostname=ingest@%h` | Consumes `ingest` queue, retailer feed sync, VLM enrichment |
| **`fashx-beat`** | ECS Fargate (single task) | `celery -A fashx.workers.app:app beat --loglevel=INFO` | Outbox relay (30s), erasure sweep (5m), nightly retention |
| **`fashx-migrate`**| ECS Fargate (one-off) | `alembic upgrade head` | Runs additive migrations before ECS service updates |

### 2.2 Supporting Infrastructure
- **Amazon RDS PostgreSQL (Multi-AZ in Mumbai)**: Private subnets, encrypted at rest, storage autoscaling.
- **Amazon ElastiCache Redis (VPC-only)**: Message broker for Celery queues and low-latency cache.
- **Amazon S3 (`fashx-media-prod`)**: Private bucket, default AES-256 encryption, public access blocked, IAM task roles.
- **Amazon ECR**: Container registry storing immutable image tags (`${{ github.sha }}`).
- **AWS Application Load Balancer (ALB) + ACM**: TLS termination, public HTTPS ingress routing to `fashx-api`.
- **AWS Secrets Manager**: Injects `DATABASE_URL`, `FASHN_API_KEY`, and auth secrets into ECS task environments.
- **Amazon CloudWatch**: Centralized JSON logging and operational alert rules.

---

## 3. Production Prerequisites & Safety Gates

1. **Production Dependencies**: Both `celery[redis]>=5.4,<6` and `gunicorn>=22,<24` are pinned in `pyproject.toml` and installed in the multi-stage Docker image.
2. **Container Image Integrity**:
   - Multi-stage Docker build produces a lean wheel distribution.
   - Dedicated non-root user (`app`, UID 10001) for least privilege.
   - Includes `alembic.ini`, `database/`, and `schemas/` so `alembic upgrade head` executes reliably.
   - `.dockerignore` blocks `.env`, local storage, tests, and temporary caches from entering the container.
3. **Provider Clearance & License Gate**:
   - Production settings reject `mock` provider (`ValueError: prod requires non-mock TRYON_PROVIDER`).
   - Production settings require `fashn_api` with `FASHN_API_KEY`; the unimplemented `fashn_selfhost` adapter raises `NotImplementedError` and is refused.
   - Commercial license assertion (`assert_production_license`) executes on startup.
4. **Network & Access Boundaries**:
   - ECS containers use AWS IAM task roles rather than static access keys (`S3_USE_IAM_ROLE=true`).
   - RDS and Redis exist strictly within private VPC subnets with ingress allowed only from ECS security groups.
   - Wildcard CORS is strictly refused in production (`wildcard CORS not allowed in prod`).

---

## 4. CI/CD Deployment Sequence (`.github/workflows/deploy.yml`)

1. **Build & Security Gate**:
   - Build container image tagged with `${{ github.sha }}`.
   - Run Trivy vulnerability scan configured with `exit-code: "1"`, failing automatically on unpatched `HIGH` or `CRITICAL` findings.
   - Push immutable tag to Amazon ECR.
2. **Automated Migration Gate**:
   - Run one-off ECS migration task definition (`fashx-migrate`) on the target cluster.
   - Poll task completion (`aws ecs wait tasks-stopped`).
   - Inspect container exit code: if exit code $\ne 0$, abort deployment immediately before touching running ECS services.
3. **Rolling Service Deployment**:
   - Update services `fashx-api`, `fashx-worker`, `fashx-ingest`, and `fashx-beat` using `--force-new-deployment`.
   - Wait for stability across all services (`aws ecs wait services-stable`).
4. **Post-Deployment Smoke Verification**:
   - Execute `python scripts/release/smoke.py --base "$API_BASE" --token "$SMOKE_TOKEN"`.
   - Verifies `/api/v1/system/health/ready`, `/api/v1/config`, `/api/v1/me`, and `/api/v1/feed`.

---

## 5. Health Checks & Observability

### 5.1 Health Check Endpoints
- **Liveness (`/healthz/live` & `/api/v1/system/health/live`)**:
  - Lightweight process check returning 200 OK without touching PostgreSQL or Redis.
  - Used by ECS container definition healthcheck.
- **Readiness (`/healthz/ready` & `/api/v1/system/health/ready`)**:
  - Validates PostgreSQL connectivity, Redis connectivity, and JWKS auth key availability.
  - Returns 503 Service Unavailable if any critical persistent dependency is degraded.
  - **VTO Provider Isolation**: The external AI provider is deliberately excluded from API readiness evaluation. An external provider disruption degrades VTO job processing, but must not take down the API or trigger ALB cascade restarts.

### 5.2 Structured JSON Logging & PII Redaction
- Configured via `fashx.core.logging.JsonFormatter` and `RedactFilter`.
- Every log message automatically scrubs:
  - Bearer JWT tokens (`eyJ...`).
  - S3 presigned URL authorization query parameters (`X-Amz-Signature=...`).
  - Base64 image payloads and raw binary data.
  - Sensitive dictionary keys (`authorization`, `token`, `password`, `secret`, `api_key`).
- VTO logs correlate via `job_id`, `trace_id`, `provider`, and safe domain error codes.

### 5.3 Operational Metrics & CloudWatch Alarms
- **Try-On Failure Rate**: $> 15\%$ over 15 minutes $\rightarrow$ Alarm & investigate vendor status.
- **Consecutive Failures**: $\ge 5$ failures $\rightarrow$ Alert on-call operator; evaluate kill switch.
- **Queue Depth**: $> 100$ jobs in `tryon` queue for 10 minutes $\rightarrow$ Worker scaling alarm.
- **Queue Latency**: P95 $> 60\text{s}$ $\rightarrow$ Worker capacity investigation.
- **API 5xx Errors**: $> 2\%$ over 5 minutes $\rightarrow$ Critical deployment rollback check.
- **Daily Budget Cap**: Exceeding daily spend limit $\rightarrow$ Automatic try-on throttle.

---

## 6. Fault Tolerance & Recovery Procedures

1. **Provider Outage**:
   - Switch `TRYON_ENABLED=false` via operator feature flag to gracefully disable new submissions while keeping mobile wardrobe and browsing intact.
   - In-flight jobs with provider collection timeouts preserve their `provider_job_id` and retry collection on backoff without resubmitting duplicate inference.
2. **Worker Termination / Spot Eviction**:
   - Unfinished jobs locked by worker lease are recovered by stale job sweepers without permanent failure states.
3. **Rollback Drill**:
   - In the event of an API or worker regression, restore the previous stable ECS task definition revision (`aws ecs update-service --task-definition fashx-api:<prev_revision>`).
   - Because all database migrations follow additive, expand-contract rules, the previous container revision remains compatible with the database schema.
4. **Database Disaster Recovery**:
   - Restore RDS instance from AWS Point-In-Time Recovery (PITR) snapshot into staging environment; verify Alembic revision before promoting.

---

## 7. Operational Test Suite

The operational readiness gates are verified via `tests/unit/test_vto_phase10_deployment.py`:
- `test_production_rejects_mock_provider`: Rejection of mock provider under production settings.
- `test_production_rejects_wildcard_cors`: Rejection of wildcard CORS.
- `test_production_requires_sql_backend`: Rejection of memory backend.
- `test_production_requires_s3_storage`: Rejection of local storage.
- `test_production_requires_s3_bucket`: Enforcement of S3 bucket name.
- `test_production_requires_jwks_auth`: Enforcement of JWKS authentication.
- `test_production_requires_privacy_and_terms`: Enforcement of legal URLs.
- `test_production_rejects_b2b_flag`: Enforcement of single-tenant MVP boundary.
- `test_production_accepts_valid_configuration`: Verification of canonical production profile.
- `test_readiness_evaluator_all_dependencies_healthy`: Verification of dependencies status reporting.
- `test_readiness_evaluator_reports_degraded_on_postgres_failure`: Verification of Postgres degradation reporting.
- `test_readiness_evaluator_reports_degraded_on_redis_failure`: Verification of Redis degradation reporting.
- `test_healthz_live_endpoint_is_lightweight`: Verification of lightweight liveness endpoint.
- `test_get_tryon_adapter_resolves_fashn_api`: Successful resolution of production Fashn API adapter.
- `test_get_tryon_adapter_refuses_unimplemented_fashn_selfhost`: Refusal of unimplemented self-host adapter.
- `test_worker_tryon_job_retry_on_redis_disconnection`: Bounded Celery retry behavior on transport drop.
- `test_log_redaction_scrubs_jwt_and_presigned_signatures`: Automatic scrubbing of JWTs and presigned signatures.
- `test_redact_filter_in_logging_pipeline`: Verification of logging filter integration.
