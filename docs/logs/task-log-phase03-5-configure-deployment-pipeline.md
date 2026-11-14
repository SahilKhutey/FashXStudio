# Task Log — Phase 03.5: Configure Deployment Pipeline

## 1. Task Metadata
- **Phase**: 03.5 Configure deployment pipeline
- **Branch**: `recovery/rc13.1-governance-correction`
- **Target Branch**: `main`
- **Pull Request**: PR #34
- **Date**: 2026-11-14

## 2. Implemented Subtasks

### 3.5.1 Review Current GitHub Actions
- Audited `.github/workflows/ci.yml`, `deploy.yml`, `deploy-staging.yml`, `deploy-production.yml`, `build-release.yml`, and `promote.yml`.
- Identified anti-patterns: silent fallback on `pip install`, weakened `pip-audit || true`, missing dedicated `integration` job, missing task definition rendering during `--force-new-deployment`, and token passed as CLI argument.

### 3.5.2 Add Dependency Installation
- Updated `.github/workflows/ci.yml` across `backend`, `integration`, `frozen`, and `api-types` jobs to use `pip install -e ".[dev]"` without silent fallback.
- Confirmed `npm ci` in `mobile` job.

### 3.5.3 Add Linting
- Configured blocking Ruff check (`ruff check .`), ESLint (`npx eslint . --max-warnings 0`), and documentation lint (`python scripts/docs_lint.py`) in CI.

### 3.5.4 Add Static Type Checks
- Configured blocking static typing via `mypy .` (backend) and `npx tsc --noEmit` (mobile).

### 3.5.5 Add Unit Tests
- Configured unit test execution in `ci.yml` using `python -m pytest tests -q -p no:cacheprovider -m "not frozen and not integration"`.
- Mobile tests run via `npx jest --ci`.

### 3.5.6 Add Integration Tests
- Created dedicated blocking `integration` job in `.github/workflows/ci.yml` running with PostgreSQL 16 (`pgvector/pgvector:pg16`) and Redis 7 service containers.
- Configured integration test execution with marker filter `-m "integration and not frozen"`.

### 3.5.7 Add Migration Checks
- Added migration validation sequence in `ci.yml`: `alembic heads`, `upgrade head`, `downgrade -1`, `upgrade head`, `alembic check`.
- Authored dedicated migration task definitions `infra/aws/ecs/task-definitions/migration-staging.json` and `migration-production.json` executing `python -m alembic upgrade head` as isolated Fargate tasks.

### 3.5.8 Add Container Build
- Audited multi-stage Dockerfile: builds wheels in stage 1, copies wheels to slim stage 2, provisions non-root UID 10001, downloads AWS RDS certificate bundle, exposes port 8000, and verifies `.dockerignore`.

### 3.5.9 Add Image Vulnerability Scan
- Added Aqua Security Trivy scan in `deploy-staging.yml` and `deploy.yml` (`aquasecurity/trivy-action@v0.28.0`), configured to fail with exit code 1 on HIGH or CRITICAL CVEs with `ignore-unfixed: true`.

### 3.5.10 Add Staging Deployment
- Authored `.github/workflows/deploy-staging.yml` triggered on `workflow_run` of `ci` on `main`.
- Renders task definitions with immutable image digest, registers them, executes database migration task to completion, deploys ECS services with circuit breaker enabled, runs smoke tests, and triggers automatic rollback on failure.

### 3.5.11 Add Health Verification After Deployment
- Hardened `scripts/release/smoke.py`:
  - Reads `SMOKE_TEST_TOKEN` from environment variable.
  - Verifies `/healthz/live` (and fallback `/api/v1/system/health/live`).
  - Verifies `/healthz/ready` (and fallback `/api/v1/system/health/ready`).
  - Verifies `/api/v1/config`.
  - Verifies authenticated identity without logging sensitive user IDs (`user_id` scrubbed).
  - Verifies discovery feed and pricing freshness timestamp.
  - Outputs summary counts and exits 0 on pass or 1 on fail.

### 3.5.12 Add Manual Production Approval
- Authored `.github/workflows/deploy-production.yml` triggered via `workflow_dispatch` with required `image_digest` input.
- Validates digest format against `^sha256:[a-f0-9]{64}$`.
- Enforces manual approval gate via protected GitHub Environment `production`.
- Verifies image exists in ECR by exact digest before proceeding.
- Executes production database migration task, rolling service updates, post-deployment smoke verification, and automated rollback on failure.

### 3.5.13 Add Rollback Procedure
- Authored `scripts/release/rollback_ecs.sh` with `set -euo pipefail`.
- Reverts ECS services to previously captured task definition ARNs (or decrements revision).
- Waits for services to stabilize via `aws ecs wait services-stable`.
- Incorporated into automated pipeline failure handlers.

### 3.5.14 Verify Secrets Never Appear in Logs
- Enforced Gitleaks secret detection in CI.
- Removed `|| true` from `pip-audit --desc on`.
- Masked sensitive tokens and identifiers in `smoke.py`.
- Task definitions use AWS Secrets Manager value references.

## 3. Concrete Task Definitions Created
- `infra/aws/ecs/task-definitions/api-staging.json`
- `infra/aws/ecs/task-definitions/migration-staging.json`
- `infra/aws/ecs/task-definitions/tryon-staging.json`
- `infra/aws/ecs/task-definitions/ingest-staging.json`
- `infra/aws/ecs/task-definitions/beat-staging.json`
- `infra/aws/ecs/task-definitions/api-production.json`
- `infra/aws/ecs/task-definitions/migration-production.json`
- `infra/aws/ecs/task-definitions/tryon-production.json`
- `infra/aws/ecs/task-definitions/ingest-production.json`
- `infra/aws/ecs/task-definitions/beat-production.json`

## 4. Documentation Authored
1. `docs/infrastructure/CI_CD_ARCHITECTURE.md`
2. `docs/infrastructure/GITHUB_ACTIONS_CONFIGURATION.md`
3. `docs/infrastructure/CI_QUALITY_GATES.md`
4. `docs/infrastructure/INTEGRATION_TEST_PIPELINE.md`
5. `docs/infrastructure/DATABASE_MIGRATION_PIPELINE.md`
6. `docs/infrastructure/CONTAINER_BUILD_AND_SCANNING.md`
7. `docs/infrastructure/ECR_IMAGE_VERSIONING.md`
8. `docs/infrastructure/ECS_DEPLOYMENT_STRATEGY.md`
9. `docs/infrastructure/STAGING_RELEASE_CHECKLIST.md`
10. `docs/infrastructure/PRODUCTION_RELEASE_CHECKLIST.md`
11. `docs/infrastructure/PRODUCTION_APPROVAL_POLICY.md`
12. `docs/infrastructure/DEPLOYMENT_SECRETS_POLICY.md`
13. `docs/infrastructure/ROLLBACK_RUNBOOK.md`
14. `docs/infrastructure/DEPLOYMENT_VERIFICATION.md`
