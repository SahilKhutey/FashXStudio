# Source Retry and Error Policy

## 1. Retry Policy Principles

Outbound requests to external catalog feeds are governed by `SourceRetryPolicy` (`backend/fashx/catalog/acquisition/retry.py`):
1. **Bounded Attempts**: A maximum of 3 attempts is enforced. Infinite retry loops are strictly prohibited.
2. **Exponential Backoff with Jitter**: Delays increase exponentially (`initial_delay * (multiplier ** attempt)`) with randomized jitter to prevent thundering herd behavior.
3. **Fail Fast on Non-Retryable Errors**: Client errors (400 Bad Request, 403 Forbidden, 404 Not Found) indicate schema or permission failures and must **never** be retried.

## 2. Retry Decision Matrix

| Failure Condition | Status Code | Policy Action |
| :--- | :--- | :--- |
| **Connection Timeout** | N/A | Retry with exponential backoff (up to 3 attempts). |
| **Connection Reset / Network Drop** | N/A | Retry with exponential backoff (up to 3 attempts). |
| **Server Error** | 500, 502, 503, 504 | Retry with exponential backoff (up to 3 attempts). |
| **Rate Limited** | 429 | Respect `Retry-After` header; wait and re-attempt. |
| **Unauthorized Token** | 401 | Invalidate cached token once and re-attempt once. If 401 repeats, fail fast. |
| **Forbidden / Revoked** | 403 | Fail immediately. Mark provider forbidden; do not retry. |
| **Invalid Client Request** | 400 | Fail immediately. Log schema mismatch. |
| **Resource Not Found** | 404 | Fail immediately. |

## 3. Granular Error Mapping

Exceptions are mapped to standard `SourceErrorCode` values (`backend/fashx/catalog/acquisition/errors.py`):
- `AUTHENTICATION`: Bad credentials, expired API keys, or repeated 401s.
- `AUTHORIZATION` / `PERMISSION_REVOKED`: 403 Forbidden or revoked contractual permissions.
- `RATE_LIMITED`: 429 Too Many Requests.
- `TRANSIENT`: Network drops, socket timeouts, 5xx gateway errors.
- `TIMEOUT`: Read or connect timeout elapsed.
- `NOT_FOUND`: Feed endpoint returns 404.
- `CURSOR_EXPIRED`: Pagination cursor invalidated by provider.
- `SCHEMA_CHANGED`: Missing required product fields or invalid payload structures.
