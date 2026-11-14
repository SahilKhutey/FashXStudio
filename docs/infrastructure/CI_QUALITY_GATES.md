# Continuous Integration Quality Gates Specification

## 1. Overview

Every Pull Request and push to `main` must pass through blocking quality gates defined in `.github/workflows/ci.yml`. In accordance with `AGENTS.md` Rule 4, no gate may be weakened (`continue-on-error`, `|| true`, or unjustified ignores are strictly prohibited).

## 2. Gate Matrix

| Gate | Tool / Command | Pass Criteria | Blocking |
| :--- | :--- | :--- | :--- |
| **Secrets Scan** | `gitleaks-action@v3` | 0 unredacted secrets or credentials detected in git history. | Yes |
| **Dependency Install** | `pip install -e ".[dev]"` | Clean installation with 0 errors. No silent fallback to base dependencies. | Yes |
| **Documentation Lint** | `python scripts/docs_lint.py` | 0 broken internal links, 0 orphaned doc references. | Yes |
| **Code Linting** | `ruff check .` | 0 errors across backend, scripts, and tests. | Yes |
| **Static Type Check** | `mypy .` | 0 type errors across backend code. | Yes |
| **Mobile Type Check** | `npx tsc --noEmit` | 0 TypeScript errors in `mobile/`. | Yes |
| **Mobile Lint** | `npx eslint . --max-warnings 0` | 0 warnings and 0 errors in React Native application. | Yes |
| **Unit Tests** | `pytest -m "not frozen and not integration"` | 100% test pass rate with 0 unhandled exceptions. | Yes |
| **Database Migrations** | `alembic heads && upgrade head && downgrade -1 && upgrade head && check` | Alembic revision head is single, reversible, and matches model metadata with 0 pending migrations. | Yes |
| **Integration Tests** | `pytest -m "integration and not frozen"` | Passes against live PostgreSQL (`pgvector/pgvector:pg16`) and Redis 7 containers. | Yes |
| **Mobile Tests** | `npx jest --ci` | 100% Jest component and unit test suite passing. | Yes |
| **Mobile Bundle Build** | `npx expo export --platform android` | React Native JavaScript bundle compiles with exit code 0. | Yes |
| **API Contract Diff** | `openapi.json` diff against `schema.d.ts` | Backend OpenAPI schema perfectly matches mobile frontend TypeScript types. | Yes |
| **Security SAST** | `bandit -r backend/fashx -ll -ii` | 0 medium or high severity security vulnerabilities. | Yes |
| **Dependency CVE Audit**| `pip-audit --desc on` | 0 known security vulnerabilities in installed Python dependencies. | Yes |

## 3. Policy on Gate Failures

1. If any blocking gate fails, the CI status is marked red (`failure`), and branch protection rules prevent merging into `main`.
2. Silent fallbacks (e.g. `pip install -e ".[dev]" || pip install -e .`) are prohibited.
3. Suppressing audit alerts with `|| true` is prohibited. If a legitimate false positive or non-vulnerable advisory occurs, an explicit justification must be recorded in the security audit log.
