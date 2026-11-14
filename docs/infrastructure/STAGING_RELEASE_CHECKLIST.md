# Staging Release Checklist

## 1. Purpose

This checklist governs the deployment and operational validation of release candidates to the `staging` environment prior to production promotion consideration.

## 2. Pre-Deployment Checks

- [ ] All CI quality gates on Pull Request passed (`.github/workflows/ci.yml`).
- [ ] Pull Request merged into `main` branch.
- [ ] Database migrations are reversible (`alembic downgrade -1` tested in CI).
- [ ] Secrets required for staging are present in AWS Secrets Manager (`fashx/staging/*`).
- [ ] ECR build completed with 0 High/Critical Trivy CVEs.

## 3. Deployment Verification

- [ ] Migration task executed in ECS Fargate with exit code `0`.
- [ ] All staging ECS services (`api`, `tryon`, `ingest`, `beat`) reported status `ACTIVE` and reached stability (`aws ecs wait services-stable`).
- [ ] Health endpoints return HTTP 200 OK:
  - `GET /healthz/live`
  - `GET /healthz/ready`
  - `GET /api/v1/config`
- [ ] Automated smoke test script executed (`python scripts/release/smoke.py --base "$API_BASE_STAGING"`).
- [ ] Synthetic test user identity check passed (`/api/v1/me`).
- [ ] Synthetic feed retrieval check passed (`/api/v1/feed?limit=20`).

## 4. Post-Deployment Soak

- [ ] Celery workers connected to staging Valkey / Redis instance and consuming from `tryon` and `ingest` queues.
- [ ] CloudWatch logs show zero recurring exceptions or connection pool exhaustion in `/fashx/staging/*` log groups.
- [ ] Release candidate soaked in staging for minimum required observation window.
