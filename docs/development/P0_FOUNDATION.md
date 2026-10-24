# FashXStudio — P0 Foundation Implementation

Status: In progress
Branch: development/p0-foundation
Scope: Engineering quality gates, reproducible local execution, migration verification and release safety.

## 1. Objective
Establish a reliable development foundation before changing catalog ingestion, recommendation ranking, virtual try-on or production identity integrations.
A passing CI workflow must represent successful execution of the checks that are declared blocking.

## 2. Required environment
- Python 3.12
- Node.js 20
- npm
- PostgreSQL with pgvector
- Redis
- Git
- Docker, where local database services are managed through containers

Use the dependency versions declared in `pyproject.toml` and `mobile/package-lock.json`.

## 3. Baseline execution
From the repository root:
```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
python scripts/docs_lint.py
ruff check .
mypy .
python -m alembic heads
python -m pytest tests -q -p no:cacheprovider -m "not frozen"
```

The lint baseline may fail initially. Capture and resolve existing violations before enabling the blocking CI gate.

Database migration checks require a configured database:
```bash
python -m alembic upgrade head
python -m alembic downgrade -1
python -m alembic upgrade head
python -m alembic check
python -m pytest tests -m db -q -rs
```
Run these commands only against a disposable development/test database. Never run destructive migration tests against production data.

Mobile validation:
```bash
cd mobile
npm ci
npx tsc --noEmit
npx eslint . --max-warnings 0
npx jest --ci
npx expo-doctor
npx expo export --platform android
```

## 4. CI changes
### Python lint
Replace the non-blocking Ruff invocation with:
```yaml
- name: Lint Python
  run: ruff check .
```
Before merging, fix all violations reported by the baseline.

### Dependency security
Run:
```bash
pip-audit --desc on
```
Resolve or formally document existing advisories before making the audit blocking. Do not suppress the audit's exit status globally.

### Frozen domains
Keep the existing frozen-domain isolation explicit. Frozen tests must become a release blocker before the associated functionality is enabled for production.

## 5. Acceptance criteria
1. Python dependencies install from the declared project configuration.
2. Documentation lint passes.
3. Ruff passes without failure suppression.
4. Mypy passes, with existing ignores reviewed and tracked.
5. Database migrations upgrade, downgrade and upgrade successfully on a disposable test database.
6. Database tests execute without unexpected skips.
7. Non-frozen backend tests pass.
8. Mobile TypeScript, ESLint and Jest pass.
9. Expo Doctor and Android bundle export pass.
10. Dependency audit findings are resolved or explicitly documented.
11. CI is green on the development branch.
12. No production credentials are stored in source code.
13. The implementation and evidence are recorded in the project status documentation.

## 6. Evidence
Record the commit SHA, CI run URL, test results, unresolved findings and reviewer approval before marking this milestone complete.
A green CI run does not prove that real catalog feeds, commercial try-on providers, cloud storage or production authentication have been configured.

## 7. Exit condition
P0.1 is complete only when the required blocking checks pass on the development branch and the evidence is recorded. Continue to P0.2 only after this condition is satisfied.
