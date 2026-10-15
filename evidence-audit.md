# Evidence audit 2026-10-15T14:28:19

## Git
branch: main   commits: 190
tags: pre-restructure-2026-10-04, v0.1-restructure-stage1, v0.10-pilot-complete, v0.2-single-backend, v0.3-auth-spine, v0.4-real-persistence, v0.5-real-tryon, v0.6-real-catalog, v0.7-discovery, v0.9-pilot-ready, v1.0-decision, v1.1-gate2, v1.2-scale-roadmap
remote branches:   origin/HEAD -> origin/main,   origin/chore/phase1-restructure,   origin/chore/phase2a-ci,   origin/chore/phase2c-freeze-mobile,   origin/docs/phase10c-pilot-report,   origin/docs/phase11a-decision,   origin/docs/phase11b-plan,   origin/docs/phase11c-narrative,   origin/docs/phase12c-gate2,   origin/feat/phase12a-operating-foundation,   origin/feat/phase12b-brand-platform,   origin/feat/phase3a-auth-core,   origin/feat/phase3b-default-deny,   origin/feat/phase3c-hardening,   origin/feat/phase4a-persistence-foundation,   origin/feat/phase4b-sql-repositories,   origin/feat/phase4c-storage-erasure,   origin/feat/phase5a-tryon-foundation,   origin/feat/phase5b-fashn-adapter,   origin/feat/phase5c-eval-decision,   origin/feat/phase6a-catalog-foundation,   origin/feat/phase6b-ingestion,   origin/feat/phase6c-enrichment-validation,   origin/feat/phase7a-discovery-eval,   origin/feat/phase7b-retrieval-latency,   origin/feat/phase7c-ranking-quality,   origin/feat/phase8a-mobile-foundation,   origin/feat/phase9a-prod-environment,   origin/main,   origin/refactor/phase2b-backend

## Expected artifacts (files, bytes, last commit). Tiny byte counts suggest stubs
ok       docs/STATUS.md                            files=1    bytes=9909     last=2026-10-12
ok       docs/adr                                  files=8    bytes=30920    last=2026-10-11
ok       docs/architecture/FROZEN.md               files=1    bytes=2783     last=2026-10-08
ok       docs/architecture/threat-model.md         files=1    bytes=1639     last=2026-10-09
ok       docs/architecture/persistence-matrix.md   files=1    bytes=4767     last=2026-10-09
ok       docs/architecture/model-licenses.md       files=1    bytes=1425     last=2026-10-10
ok       docs/architecture/catalog-sources.md      files=1    bytes=3023     last=2026-10-10
ok       docs/logs                                 files=39   bytes=248786   last=2026-10-12
ok       docs/release                              files=2    bytes=7151     last=2026-10-11
ok       docs/runbooks                             files=11   bytes=33613    last=2026-10-12
ok       docs/legal                                files=11   bytes=37100    last=2026-10-12
ok       docs/pilot                                files=18   bytes=96917    last=2026-10-12
ok       docs/strategy                             files=18   bytes=105476   last=2026-10-12
ok       docs/operations                           files=15   bytes=51008    last=2026-10-12
ok       backend/fashx/security                    files=11   bytes=24171    last=2026-10-11
ok       tests/security                            files=12   bytes=43587    last=2026-10-13
ok       tests/contracts                           files=10   bytes=19058    last=2026-10-13
ok       eval/personas.yml                         files=1    bytes=3342     last=2026-10-10
ok       eval/judgments.csv                        files=1    bytes=18906    last=2026-10-10
ok       gold                                      files=1    bytes=35150    last=2026-10-10
ok       mobile/app.config.ts                      files=1    bytes=1155     last=2026-10-11
MISSING  mobile/.maestro
ok       .github/workflows                         files=2    bytes=6991     last=2026-10-13
ok       static/widget                             files=1    bytes=14828    last=2026-10-12
ok       apps/api                                  files=36   bytes=48788    last=2026-09-19

## Things that can be weakened to make CI green
# noqa: 20
# type: ignore: 67
pytest skip / xfail: 1
workflows: continue-on-error / '|| true': 4
mypy ignore_errors lines: 5
ruff ignores:
  ignore = [
  [lint.per-file-ignores]

## Tests (MVP, frozen excluded)
Note: Local Windows host does not have Postgres daemon running; CI runs with pgvector container.
CI execution on main (run 38350544833): 1193 passed, 244 deselected in 31.66s.
collected (all):

======================== 1437 tests collected in 3.83s ========================
security tests collected:

========================= 68 tests collected in 2.25s =========================

## Migrations
heads:
0025_b2b_multi_tenant (head)
check: (requires active Postgres service container; in CI: 0 unhandled schema diffs)

## Large files and images in data folders
image files tracked under gold/ eval/ static/: 0

## Sensitive strings in workflows (counts only)
AWS account-id style ARNs under .github: 0
README mentions PYTHONPATH/1271/Verified: 0

## Secrets across all refs
gitleaks not installed; skipped
