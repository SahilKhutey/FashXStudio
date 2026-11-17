# Developer Log — Phase 03.5: Configure Deployment Pipeline

## 1. Engineering Scope and Goals
Phase 03.5 establishes a secure, repeatable, and automated deployment pipeline for FashXStudio on AWS (`ap-south-1` Mumbai) using GitHub Actions, Amazon ECR, and Amazon ECS Fargate.

The implementation addresses the requirements across 14 discrete subtasks (3.5.1 to 3.5.14):
1. Review current GitHub Actions (`ci.yml`, `deploy.yml`, `build-release.yml`, `promote.yml`).
2. Add dependency installation (`pip install -e ".[dev]"` without silent fallback; `npm ci` in `mobile/`).
3. Add linting (`ruff check .`, `eslint .`, `docs_lint.py`).
4. Add static type checks (`mypy .`, `npx tsc --noEmit`).
5. Add unit tests (`not frozen and not integration`, Jest).
6. Add integration tests (dedicated blocking CI job with PostgreSQL `pgvector:pg16` and Redis 7 service containers).
7. Add migration checks (`alembic heads`, `upgrade head`, `downgrade -1`, `upgrade head`, `alembic check`).
8. Add container build (multi-stage build, non-root user UID 10001, AWS RDS SSL trust bundle).
9. Add image vulnerability scan (Aqua Security Trivy blocking on High/Critical CVEs).
10. Add staging deployment (`deploy-staging.yml` rendering task definitions with image digest and deploying to ECS).
11. Add health verification after deployment (`smoke.py` checking `/healthz/live`, `/healthz/ready`, config, and scrubbed identity/feed checks).
12. Add manual production approval (`deploy-production.yml` with regex digest validation and protected GitHub environment approval).
13. Add rollback procedure (`scripts/release/rollback_ecs.sh` with state capture and ECS deployment circuit breakers).
14. Verify secrets never appear in logs (Gitleaks, `pip-audit --desc on` without `|| true`, sanitized output in `smoke.py`).

## 2. Key Architecture Decisions
- **Immutable Container Promotion**: The pipeline builds an image once on `main`, captures its cryptographic digest (`sha256:...`), deploys that exact digest to staging, and promotes that identical digest to production without rebuilding.
- **Fail-Fast CI Dependencies**: Removed silent fallback (`pip install -e ".[dev]" || pip install -e .`), ensuring CI fails immediately if dev dependencies fail to install.
- **Uncompromised Quality Gates**: Removed `|| true` from `pip-audit --desc on` in `ci.yml`, adhering strictly to `AGENTS.md` Rule 4.
- **Isolated Migration Runner**: In staging and production, database migrations are executed as one-off ECS Fargate tasks using dedicated migration IAM credentials and task definitions (`migration-staging.json` / `migration-production.json`), waiting for exit code 0 before updating application services.
- **Circuit Breaker & Rollback Scripting**: Workflows record existing service task definitions prior to update and trigger `scripts/release/rollback_ecs.sh` upon failure, alongside ECS native deployment circuit breakers.
- **Credential Sanitization**: `smoke.py` reads tokens from `SMOKE_TEST_TOKEN` (avoiding CLI exposure) and strips user IDs from logs.

## 3. Environment Disclosures (AGENTS.md Rule 14)
- Live AWS deployments require human founder credentials and AWS OIDC setup.
- Container builds and deployments in GitHub Actions will run on GitHub-hosted Ubuntu runners assuming AWS IAM roles when provisioned.
- Local verification was performed against local Python 3.12 test suites, docs lint, and static analysis tools.
