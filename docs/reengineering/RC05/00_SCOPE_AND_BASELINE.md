# RC05 — 00 Scope and Baseline

## Objective
Establish an unambiguous, verified baseline for the Virtual Try-On (VTO) subsystem following the completion of RC03 (End-to-End System Integration) and RC04 (Consumer Experience Polish), ensuring all RC05 engineering activities build upon stable foundations.

## Existing State
- **Base Repository:** `SahilKhutey/FashXStudio`
- **Base Branch:** `main` at `db2609e4a8ae3c6fe687c03d81e54ddad86d1f59`
- Prior cycles completed and merged:
  - PR #26 (RC-03): System integration, feed, closet persistence, affiliate commerce handoff.
  - PR #27 (RC-04): Settings & privacy management, account erasure, LAN device configuration.
- Existing VTO components:
  - Backend try-on router (`backend/fashx/tryon/router.py`)
  - Use cases: `SubmitTryOnJobUseCase`, `GetTryOnJobStatusUseCase`, `ProcessTryOnJobUseCase`
  - Polling worker: `TryOnWorker` (`backend/fashx/tryon/application/worker.py`)
  - Adapters: `MockTryOnAdapter`, `FashnApiAdapter`
  - Mobile client: `useTryOn.ts`, `tryonApi.ts`, `mobile/app/tryon/[jobId].tsx`

## Changes
- Baseline verification of all existing VTO test suites.
- Created implementation branch `recovery/rc05-vto-integration` from `origin/main` (`db2609e`).
- Established testing protocol for Windows environments accounting for `aiosqlite` loopback socket boundaries.

## Contracts
- Base commit API contracts preserved for all VTO endpoints:
  - `POST /api/v1/tryon/jobs` (`Idempotency-Key` header, returns 202 Accepted)
  - `GET /api/v1/tryon/jobs/{job_id}` (Returns `TryOnJobStatusResponse`)
  - `GET /api/v1/tryon/jobs` (Returns `list[TryOnJobListItem]`)
  - `GET /api/v1/tryon/artifacts/{artifact_key}` (Returns `TryOnArtifactResponse`)
  - `POST /api/v1/feedback/tryon` (Returns 201 Created)

## Implementation
- Environment configured with Python 3.12 (`.venv`), Node 20 (`mobile/`).
- Automated baseline test runners validated.

## Execution
```bash
# Verify baseline commit
git switch recovery/rc05-vto-integration
git rev-parse HEAD # db2609e4a8ae3c6fe687c03d81e54ddad86d1f59
```

## Tests
- Baseline unit test pass: 90/90 passed
- Baseline mobile test pass: 21 suites, 152 tests passed
- Baseline TypeScript typecheck: 0 errors

## Risks
- Running worker processes and API server against unsynchronized databases.
- Mitigation: All state transitions verified with transactional fixtures and deterministic locks.

## Evidence
```
Baseline Backend Tests: 90 passed, 1 warning in 35.34s
Baseline Mobile Tests: 21 passed, 152 passed in 14.21s
Baseline TypeScript: 0 errors (clean exit 0)
```

## Exit Criteria
- Clean baseline branch established.
- All pre-existing test suites execute green.
- Readiness to begin RC05.1 provider configuration.
