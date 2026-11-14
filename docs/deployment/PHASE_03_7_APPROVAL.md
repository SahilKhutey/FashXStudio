# Phase 03.7 — Backend Deployment Validation Approval Specification

## 1. Executive Summary

Phase 03.7 establishes the deployment verification standards and automated test harnesses for the FashXStudio backend deployed to staging on AWS Mumbai (`ap-south-1`).

This specification outlines the acceptance criteria, evidence reporting formats, quality gates, and approval procedures across all eleven verification domains (3.7.1 to 3.7.11).

## 2. Complete Verification Matrix

| ID | Domain | Validation Method | Automated Tool / Script | Pass Condition |
| :--- | :--- | :--- | :--- | :--- |
| **3.7.1** | **API Deployment** | ECS Task Inspection | `.github/workflows/deploy-staging.yml` | Immutable ECR image digest matches release artifact; running count = desired count. |
| **3.7.2** | **Health Endpoints**| HTTP Smoke Test | `scripts/staging/validate_deployment.py` | `/healthz/live` and `/healthz/ready` return HTTP 200 without exposing secrets. |
| **3.7.3** | **PostgreSQL** | SQL Integration Test | `scripts/staging/validate_database.py` | `SELECT 1` passes; temporary table read/write succeeds; pool healthy. |
| **3.7.4** | **Redis / Valkey** | Broker Integration Test | `scripts/staging/validate_redis.py` | PING succeeds; ephemeral key round-trip passes; queue lengths inspectable. |
| **3.7.5** | **Object Storage** | S3 Adapter Test | `scripts/staging/validate_storage.py` | Put/get/delete round-trip succeeds; public access blocked; KMS encrypted. |
| **3.7.6** | **Workers** | Celery Task Test | `scripts/staging/validate_workers.py` | Real worker processes diagnostic tasks (`fashx.validation.ping`); retries bounded. |
| **3.7.7** | **Migrations** | Alembic State Check | `scripts/staging/validate_migrations.py` | Single migration head verified; database revision matches release; no schema drift. |
| **3.7.8** | **Logs & Tracing** | CloudWatch & Context | `scripts/staging/validate_logs.py` | Single-line JSON format valid; request ID & traceparent correlated; secrets scrubbed. |
| **3.7.9** | **Restart** | Resilience Test | `scripts/staging/validate_restart.py` | `task_acks_late=True`; replacement tasks stabilize without dropped jobs. |
| **3.7.10**| **Backup & Restore**| RDS Snapshot Drill | `scripts/staging/validate_backup_restore.py` | Manual snapshot restored to temporary instance; schema verified; instance cleaned up. |
| **3.7.11**| **Rollback** | ECS Rollback Drill | `scripts/staging/validate_rollback.py` | State capture verified; `rollback_ecs.sh` reverts services to previous healthy task ARNs. |

## 3. Evidence Record Format

Each automated test produces a standardized JSON record in `reports/staging/`:

```json
{
  "phase": "03.7",
  "environment": "staging",
  "test_id": "3.7.3",
  "test_name": "database_connectivity",
  "status": "PASS",
  "started_at": "2026-11-14T05:20:00Z",
  "completed_at": "2026-11-14T05:20:01Z",
  "steps": [
    {"step": "ping", "status": "PASS", "duration_ms": 1.2},
    {"step": "ephemeral_write_read", "status": "PASS", "duration_ms": 2.5},
    {"step": "pool_inspection", "status": "PASS", "pool_metrics": {"size": 10, "checked_in": 1, "checked_out": 0}}
  ]
}
```

## 4. Governance & Environment Disclosures (AGENTS.md Rules 1, 2, 14)

1. **Human Evidence Boundary (Rule 1)**: In accordance with repository governance, coding agents do not create or edit files in `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md`. Live production or staging run evidence cards must be collected and committed by the human founder.
2. **No Simulated Passes (Rule 2)**: Test results and pass statuses in this repository must originate from real command outputs executed against the environment.
3. **Infrastructure Prerequisites (Rule 14)**: Live AWS verification on ECS Fargate, RDS, ElastiCache, and S3 requires the human founder to provision the cloud infrastructure and configure AWS OIDC credentials in GitHub Actions. Local verification of all automation scripts and unit/integration test suites is 100% complete and passing.

## 5. Exit Gate Checklist

- [ ] All 11 automated test suites in `tests/deployment/` pass in CI.
- [ ] All 10 staging validation scripts in `scripts/staging/` execute cleanly.
- [ ] Workflow `.github/workflows/staging-validation.yml` configured and ready.
- [ ] Live AWS staging deployment executed by founder with real image digest captured.
- [ ] Live backup restoration drill executed by founder on temporary RDS instance.
- [ ] No unhandled critical vulnerabilities or credential leaks in logs.
