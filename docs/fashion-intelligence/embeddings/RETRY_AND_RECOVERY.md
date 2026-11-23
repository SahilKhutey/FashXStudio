# Fashion Image Embedding Retry & Recovery Strategy

## 1. Failure Modes and Classification

| Category | Typical Cause | Strategy | Max Retries |
| :--- | :--- | :--- | :--- |
| **Transient I/O** | Storage bucket read timeout, DB lock | Exponential backoff with jitter | 3 |
| **Compute Timeout**| Worker thread contention, GPU stall | Worker restart, retry on separate worker | 2 |
| **Permanent Corrupt**| Truncated image file, invalid header | Mark `FAILED`, log quarantine, no retry | 0 |
| **Permission Revoked**| Merchant `IMAGE_AI_PROCESS` revoked | Skip immediately, audit log | 0 |
| **Validation Reject**| Dimension mismatch, non-finite float | Dead-letter queue, alert engineering | 0 |

---

## 2. Exponential Backoff Formula
For transient failures:
$$T_{\text{wait}} = \min\left(T_{\text{max}}, T_{\text{base}} \times 2^{\text{attempt}} + \text{uniform}(0, \text{jitter})\right)$$
- $T_{\text{base}} = 1.0\text{ second}$
- $T_{\text{max}} = 30.0\text{ seconds}$
- $\text{jitter} = 0.5\text{ seconds}$

---

## 3. Dead-Letter Queue (DLQ) & Circuit Breaker
- When an image fails 3 consecutive attempts or fails with a non-recoverable validation error, an entry is written to `embedding_jobs` with `status='FAILED'` and the diagnostic traceback in `last_error`.
- If a batch experiences >20% failure rate, a circuit breaker trips, pausing the batch runner and raising an alert to prevent catalog ingestion deadlocks.
