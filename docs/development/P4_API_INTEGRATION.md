# P4 — API Integration Foundation and Typed Data Layer
Project: FashXStudio  
Milestone: P4  
Status: Implemented & Tested

## Purpose and Scope
Establish a unified, type-safe API client and data layer connecting FashXStudio's mobile application to the FastAPI backend. It provides predictable TypeScript error types, robust network failure and abort/timeout normalization, safe single-attempt token refresh, and standardized React Query retry policies across Feed, Wardrobe, Closet, and Profile features.

## Architecture and Core Modules
1. **Error Contract (`mobile/src/api/errors.ts`)**:
   - `ApiErrorKind`: `"http" | "network" | "timeout" | "invalid_response"`.
   - `ApiError`: Extends `Error` with `status`, `code`, `detail`, optional `requestId`, and `kind`.
   - `isUnauthorized`: Boolean property identifying HTTP 401.
   - `isRetryable`: Boolean property identifying transient errors (`network`, `timeout`, HTTP 408, 429, >=500).
   - `toApiError(error: unknown)`: Normalizes `AbortError` / `TimeoutError` into `timeout` kind and network exceptions into `network` kind.

2. **Hardened API Client (`mobile/src/api/client.ts`)**:
   - URL path validation enforcing relative endpoints starting with `/`.
   - Bearer authentication via `getAccessToken()`.
   - 204 No Content parsing returning `undefined`.
   - Content-Type verification accepting `application/json` and `+json`.
   - Malformed/non-JSON response guards throwing structured `invalid_response` errors.
   - Idempotency key forwarding via `Idempotency-Key` header.
   - Safe session refresh on 401:
     - Developer tokens (`getDevToken()`) are never refreshed.
     - Unsafe non-idempotent requests (POST without `idempotencyKey`) are rejected without retry to avoid duplicate operations.
     - Safe requests (GET, HEAD, or idempotent mutations) execute a single refresh via `supabase.auth.refreshSession()`.
     - Refresh failure immediately triggers `supabase.auth.signOut()` and throws `unauthorized`.

3. **React Query Integration (`mobile/src/app-shell/AppProviders.tsx`)**:
   - `queryRetry`: Custom retry evaluator using `error.isRetryable` up to 2 attempts for queries.
   - Queries configured with 60s stale time; mutations set to `retry: false` to prevent accidental re-execution.

4. **Typed Feature APIs (`mobile/src/features/wardrobe/`, `mobile/src/features/closet/`)**:
   - `mobile/src/features/wardrobe/api.ts`: Typed API functions (`fetchUserWardrobe`, `saveGarmentToWardrobe`, `removeGarmentFromWardrobe`).
   - `mobile/src/features/wardrobe/hooks.ts`: Query and mutation wrappers with cache invalidation (`queryKey: ["wardrobe"]`).
   - `mobile/src/features/closet/`: Re-exports wardrobe APIs and hooks to maintain compatibility without duplicating implementations.

## OpenAPI Contract Generation
The mobile TypeScript schema is auto-generated directly from FastAPI's OpenAPI specification:
```bash
python -c "import json; from fashx.main import app; open('openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
npx --prefix mobile openapi-typescript openapi.json -o mobile/src/api/schema.d.ts
```
The output path `mobile/src/api/schema.d.ts` matches the contract enforced by GitHub Actions CI (`api-types` job).

## Verification Results

| Check / Test Suite | Command | Result |
|---|---|---|
| Docs Lint | `python scripts/docs_lint.py` | `docs lint ok` |
| Python Ruff Linter | `ruff check .` | `All checks passed!` |
| Python Mypy | `mypy .` | `Success: no issues found in 987 source files` |
| Mobile ESLint | `cd mobile; npx eslint . --max-warnings 0; cd ..` | 0 errors, 0 warnings |
| Mobile TypeScript | `cd mobile; npx tsc --noEmit; cd ..` | 0 errors |
| Mobile Jest Test Suites | `cd mobile; npx jest --ci; cd ..` | 12 passed, 12 total (97 tests) |
| Android Expo Export | `cd mobile; npx expo export --platform android; cd ..` | 1591 modules bundled, exported to dist |
| Backend Contract Tests | `python -m pytest tests/contracts tests/unit/test_schema_contracts.py` | 41 passed |

## Milestone Completion Status

| Capability | Implemented | Unit Tested | Verified End-to-End |
|---|---|---|---|
| Hardened API Client | Yes | Yes (12 test cases) | Mock & Contract Validated |
| Normalized Error Contract | Yes | Yes | Mock & Contract Validated |
| 401 Safe Session Refresh | Yes | Yes | Mock Validated |
| React Query Retry Policy | Yes | Yes | Mock Validated |
| Generated OpenAPI Schema | Yes | Yes | Verified Against Backend Schema |
| Feature Hooks (Feed, Wardrobe) | Yes | Yes | Contract Validated |
| Real Cloud Backend End-to-End | Pending | Pending | Blocked (no cloud staging environment configured) |

## Known Blockers & Limitations (Rule 14)
- **Supabase Production Project**: Session refresh and authentication logic are verified via Jest mocks; live Supabase project credentials are not connected locally.
- **Hosted PostgreSQL**: Backend database tests run against SQLite/mock in local Windows environment; PostgreSQL verification is executed in CI.
- **Physical Mobile Device**: Testing was performed through Jest test suites, Expo CLI static bundling, and TypeScript validation; physical Android/iOS hardware test remains unverified.
