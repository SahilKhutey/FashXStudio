# RC08 — CI/CD & Deployment Automation

## 1. Automated Pipeline Stages
Every Pull Request and main push triggers `.github/workflows/ci.yml`:
1. **Secrets Scan**: `gitleaks/gitleaks-action@v3` (blocks on leaked tokens or API keys).
2. **Backend**:
   - `docs_lint.py` (documentation integrity).
   - `ruff check .` (Python linting).
   - `mypy .` (static typing).
   - `alembic heads -> upgrade head -> downgrade -1 -> upgrade head -> check` against real PostgreSQL 16.
   - `pytest -m db` (mandatory database tests).
   - `pytest -m "not frozen"` (full backend unit and integration regression).
3. **Mobile**:
   - `npm ci`.
   - `npx tsc --noEmit`.
   - `npx eslint . --max-warnings 0`.
   - `npx jest --ci`.
4. **Security**: Default-deny routing and tenant isolation checks.
5. **Frozen**: Isolated verification of unmounted future commerce domains.

## 2. Staging Deployment Pipeline (`rc08-staging.yml`)
Upon merge to `recovery/rc08-staging-pilot-readiness` or manual dispatch:
1. Build immutable container image tagged with `git rev-parse --short HEAD`.
2. Run vulnerability container scan (Trivy / Snyk).
3. Push image to private container registry (ECR / GHCR).
4. Deploy container image to staging ECS / App Platform with injected secrets.
5. Execute migration step via task runner.
6. Run `/healthz/ready` probe and staging smoke tests.
7. Rollback immediately if health check fails within 3 minutes.
