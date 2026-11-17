# Production Release Checklist

## 1. Purpose

This checklist governs the manual promotion of an immutable container image digest from staging to the live `production` environment.

## 2. Pre-Promotion Verification

- [ ] Release candidate successfully deployed to `staging` and verified with `smoke.py`.
- [ ] Image digest retrieved from staging build output (`sha256:[a-f0-9]{64}`).
- [ ] Image digest verified to exist in private Amazon ECR (`aws ecr describe-images`).
- [ ] Database migration is backward-compatible with the currently running production version (Expand phase).
- [ ] AWS RDS automated backup is confirmed healthy and recent.
- [ ] Production Secrets in AWS Secrets Manager (`fashx/prod/*`) verified for any new required configuration.

## 3. Approval and Execution

- [ ] Founder / Release Manager approved deployment in GitHub Environment `production`.
- [ ] Production deployment workflow triggered via `workflow_dispatch` (`.github/workflows/deploy-production.yml`).
- [ ] Production Alembic migration task executed in ECS Fargate with exit code `0`.
- [ ] Rolling update of production ECS services (`fashx-prod-api`, `fashx-prod-tryon`, `fashx-prod-ingest`, `fashx-prod-beat`) achieved stability (`aws ecs wait services-stable`).

## 4. Post-Promotion Verification

- [ ] Automated smoke test executed against production API endpoint (`python scripts/release/smoke.py --base "$API_BASE_PROD"`).
- [ ] Public liveness and readiness probes return HTTP 200 OK (`/healthz/live`, `/healthz/ready`).
- [ ] Outbound attribution and discovery feed verified.
- [ ] CloudWatch ALB target group metrics show 100% healthy host count.
- [ ] Zero unhandled 5xx errors in CloudWatch `/fashx/prod/api` logs during initial 15-minute observation window.
- [ ] Sentry / error tracker error rate within normal baseline.
