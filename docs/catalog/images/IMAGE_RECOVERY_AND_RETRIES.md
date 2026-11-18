# Image Recovery and Retries

## 1. Failure Stratification and Handling

| Failure Code | Root Cause | Retry Policy | Outcome |
| :--- | :--- | :--- | :--- |
| `not_found` | HTTP 404 / 410 from origin | No retry | Logged; product ingested without image asset. |
| `rate_limited` | HTTP 429 from origin | Backoff using `Retry-After` header | Rescheduled with jitter. |
| `server_error` | HTTP 500 / 502 / 503 | Max 3 attempts with exponential backoff | Bounded retry before marking unretrievable. |
| `timeout` | Connection / Read timeout | Max 3 attempts | Transient retry. |
| `decompression_bomb` | Pillow pixel limit violation | Never retry | Hard rejection; safety violation logged. |
| `corrupted_image` | Byte stream unreadable | Never retry | Hard rejection. |
| `db_commit_failed` | DB flush exception post-upload | Compensation cleanup | S3 objects unlinked and cleaned up. |

---

## 2. Idempotent Retry Safety

Retrying an identical image job is idempotent. It verifies hash matches and reuses existing asset entities without creating redundant rows or leaking orphaned S3 keys.
