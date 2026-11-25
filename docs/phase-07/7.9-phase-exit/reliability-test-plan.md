# Phase 07 Reliability & Failure Injection Test Plan

## 1. Reliability Objectives

The FashXStudio VTO reliability architecture ensures that jobs never disappear, never execute paid inference twice due to duplicate queue delivery, and recover predictably from worker termination, network partitions, or provider outages.

---

## 2. State Machine Integrity

The state machine (`backend/fashx/tryon/lifecycle/states.py`) enforces strict transition rules:

```
[CREATED] ------------> [VALIDATING] ------------> [QUEUED]
                              |                       |
                              v                       v
                         [CANCELLED]             [CANCELLED]
                              ^                       ^
                              |                       |
                         [CANCEL_REQ] <---------------+
                              ^                       |
                              |                       v
                         [CANCEL_REQ] <--------- [PROCESSING] <---> [RETRY_PENDING]
                                                      |                     |
                                                      v                     v
                                            [SUBMISSION_UNKNOWN]         [FAILED]
                                                      |
                                                      v
                                            [OUTPUT_VALIDATING]
                                                      |
                                                      v
                                              [STORING_RESULT]
                                                      |
                                                      v
                                                 [COMPLETED]
                                                      |
                                                      v
                                                  [EXPIRED]
```

### Invariants:
1. **No Jumping**: Transition directly from `CREATED` to `COMPLETED` is strictly prohibited (`InvalidJobTransition`).
2. **Terminal Permanence**: Terminal states (`COMPLETED`, `FAILED`, `CANCELLED`) can never transition back to `PROCESSING` or `QUEUED`.
3. **Lease Protection**: A job in `PROCESSING` must be actively leased by a worker; if the lease expires without heartbeat, the stuck-job recovery sweep resets it or routes to DLQ.

---

## 3. Failure Injection Matrix (14 Scenarios)

| # | Failure Scenario | Injected Condition | Expected Behavior & Recovery | Automated Test Reference |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Provider Rate Limit (429)** | Provider returns HTTP 429 Too Many Requests | Job transitions to `RETRY_PENDING`; exponential backoff applied (base 5s, factor 2, max 3 retries). | `test_retry_policy.py`<br>`test_messaging_temporary_provider_failure` |
| **2** | **Provider Internal Error (500)** | Provider returns HTTP 500/503 | Classified as transient error; retry scheduled if attempt count < 3. | `test_retry_policy.py` |
| **3** | **Network Timeout Pre-Submit** | Socket timeout before HTTP headers sent | No provider request ID exists; safe to retry; job re-enqueued. | `test_provider_attempts_and_worker.py` |
| **4** | **Ambiguous Paid Submission** | Connection drops during read after submission | Job marked `SUBMISSION_UNKNOWN`. Worker does NOT re-submit; sweeper reconciles with provider by request ID. | `test_state_machine.py`<br>`test_recovery_and_dlq.py` |
| **5** | **Provider Polling Failure** | Status poll returns 504 Gateway Timeout | Retry polling with exponential jitter; does not create a duplicate generation request. | `test_provider_attempts_and_worker.py` |
| **6** | **Malformed Provider Output** | Provider returns invalid JSON or missing image URL | Classified as provider error; transitions to `FAILED` with code `PROVIDER_MALFORMED_OUTPUT`. | `test_output_validation.py` |
| **7** | **Output Download Interruption** | Image download stream aborts mid-transfer | Download retried up to 2 times; if corrupted, job marked `FAILED`. | `test_output_validation.py` |
| **8** | **S3 Write Failure** | AWS S3 returns 500 SlowDown or AccessDenied | Retried with backoff; does not re-run inference since image bytes are buffered locally. | `test_output_validation.py` |
| **9** | **Database Failure Mid-Job** | PostgreSQL connection pool exhausted | Celery worker rejects task (nack); transaction rollback; task requeued. | `test_recovery_and_dlq.py` |
| **10** | **Worker Crash During Run** | `SIGKILL` sent to worker process during processing | Lease expires after 300s. Lease sweeper detects dead worker and re-enqueues job. | `test_leases_and_timeouts.py` |
| **11** | **Queue Duplicate Delivery** | Same queue message delivered to two workers | Database row lock (`SELECT FOR UPDATE NOWAIT`) ensures only one worker acquires lease; second worker exits gracefully. | `test_messages_and_duplicates.py` |
| **12** | **Shopper Cancels In-Flight** | Shopper requests cancellation during inference | Job status set to `CANCEL_REQUESTED`; worker halts processing upon next step; result discarded. | `test_cancellation.py` |
| **13** | **Catalog Delisting Mid-Job** | Merchant removes garment offer before inference | Time-of-Use guard halts job; marked `FAILED` with `PRODUCT_UNAVAILABLE`. | `test_time_of_use_guard.py` |
| **14** | **Consent Revocation Mid-Job** | Shopper withdraws biometric consent before inference | Time-of-Use guard halts job; marked `FAILED` with `CONSENT_REVOKED`; zero egress to provider. | `test_vto_worker_time_of_use_recheck_blocks_revoked_consent` |

---

## 4. Dead-Letter Queue (DLQ) Governance

When a job exhausts its maximum retry count (3 attempts) or encounters an unrecoverable fatal error:
1. Job state transitions to `FAILED`.
2. Error details, safe non-confidential payloads, and execution history are written to the `tryon_dead_letters` table.
3. Alert `tryon_dead_letters_open` is published to operational monitoring.
4. An operator runbook procedure exists for re-driving dead letters once root causes are resolved.
