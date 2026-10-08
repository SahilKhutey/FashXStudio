# Restructure Guide

## Order of operations
1. **Stage 1 (safe, non-code):** `bash scripts/restructure_stage1.sh` (dry run) → review → `--apply`. Tag `pre-restructure-2026-10-04` is created for rollback.
2. Copy in `README.md`, `docs/STATUS.md`, `docs/adr/0001-...md`, `.github/workflows/ci.yml`. Commit: `chore: stage 1 restructure + honest status`.
3. Fix doc links:
   `grep -rn "docs/task-log\|docs/visual-design\|release-readiness\|Foundation/" . --include="*.md" --include="*.yml"`
4. Run `seed_github_issues.sh` to create labels, milestones and the backlog.

## Stage 2 (code moves) - do manually, on a branch, tests green after EVERY step
**First, diagnose the likely import collision.** Docs say tests run with `PYTHONPATH=".;api"`, and both root `app/` and `api/app/` appear to exist. Two top-level packages named `app` resolve by path order and can shadow each other.
```
find . -name "__init__.py" -path "*/app/*" -maxdepth 3
grep -rn "^from app\|^import app" --include="*.py" . | cut -d: -f1 | sort | uniq -c | sort -rn | head
```
Then:
1. Pick `backend/fashx` as the single package. `git mv` one subpackage at a time (`domain/`, `repositories/`, `api/v1/`, `integration/`, `observability/`, `security/`, `features/`), rewrite imports with `ruff`/`sed`, run `pytest` after each, commit each.
2. Move `api/app/main.py` to `backend/fashx/api/main.py`; update Dockerfile, Makefile, README quickstart, uvicorn path, CI `PYTHONPATH`.
3. Freeze: move C05-C11 domains into `backend/fashx/domain/frozen/` (or flag-gate), remove their routers from the main app, keep their tests under `tests/frozen/` and exclude from the required CI job.
4. Mobile: diff `mobile/` vs `apps/mobile`; keep the one with real navigation/state; port leftovers; delete the other.
5. Delete empty dirs; update `.dockerignore`, `pyproject.toml` package paths, `mypy.ini`, `ruff.toml`, `pytest.ini`.

## Rollback
`git reset --hard pre-restructure-2026-10-04` (or `git checkout main`; work is on branches).
