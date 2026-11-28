# 05 — API Client Architecture

## Centralized Client (`mobile/src/api/client.ts`)
- Prefixes all relative paths with `/api/v1` and rejects non-relative or protocol-relative paths (`invalid_api_path`).
- Attaches `Accept: application/json`, `X-Request-ID` correlation header, `Authorization: Bearer <token>`, and optional `Idempotency-Key`.
- Enforces configurable `AbortController` timeouts (default `20_000` ms) normalized to `ApiError(..., "request_timeout", ..., "timeout")`.
- Handles HTTP `204` without JSON parsing and normalizes structured HTTP/network errors via `mobile/src/api/errors.ts`.
- Performs single-flight 401 token refresh + one retry **only** for idempotent `GET`/`HEAD` or requests with an explicit `Idempotency-Key` (never retries non-idempotent `POST` blindly).
- Zod response validation boundary added in `mobile/src/api/schemas/product.schema.ts` (`ProductSummarySchema`).

## Verification
- Verified by `mobile/src/api/client.test.ts` and `mobile/__tests__/phase09_1_foundation.test.ts`.
