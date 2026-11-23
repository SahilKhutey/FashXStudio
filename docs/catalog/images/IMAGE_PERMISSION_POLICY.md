# Image Permission Policy

## 1. Granular Image Rights Matrix

Every image operation requires explicit authorization from the contractual permissions engine.

| Operation | Required Permission Code | Failure Behavior |
| :--- | :--- | :--- |
| Read product image reference | `PRODUCT_DATA_READ` | Record rejected; no network fetch attempted. |
| Download source image bytes | `IMAGE_FETCH` | Download refused; error `permission_denied_fetch`. |
| Retain original image bytes | `IMAGE_STORE` | Original bytes discarded; only permitted derivatives stored. |
| Display image in consumer UI | `IMAGE_DISPLAY` | `display_eligible = False`; no public display derivatives created. |
| Create display derivative | `DERIVATIVE_CREATE` | Display variant generation skipped. |
| Retain display derivative | `DERIVATIVE_STORE` | Display variants not persisted to S3. |
| Use image in AI service | `IMAGE_AI_PROCESS` | Prohibited from ingestion into ML/embedding models. |
| Virtual try-on processing | `VTO_PROCESS` | `tryon_eligible = False`; excluded from try-on pipelines. |
| Create VTO derivative | `DERIVATIVE_CREATE` | VTO PNG input not generated. |
| Retain VTO derivative | `DERIVATIVE_STORE` | VTO input not stored in S3. |

---

## 2. Fail-Closed Invariant

- If the permission service is unavailable, database connection drops, or evidence is missing, permissions evaluate to `allowed = False`.
- Authorization checks are re-evaluated immediately before each sensitive operation (particularly after asynchronous queue waits).
