# 09 — Token Refresh

## Implementation
- `refreshSessionOnce()` (`mobile/src/auth/refresh-manager.ts`) coalesces concurrent refresh calls into a single in-flight promise.
- `mobile/src/api/client.ts` refreshes once on `401` only for idempotent `GET`/`HEAD` or requests with an explicit `Idempotency-Key` (never blind-retrying non-idempotent `POST` requests such as VTO submissions).
- `403` permission errors never trigger token refresh.
