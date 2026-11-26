# Phase 07 Operational Monitoring & Incident Runbook

## 1. Monitoring & Observability Architecture

The Virtual Try-On (VTO) subsystem exports Prometheus-compatible metrics and structured logs to provide immediate visibility into demand, latency, provider errors, and financial burn.

### 1.1 Required Telemetry Metrics

| Metric Name | Type | Labels | Operational Purpose |
| :--- | :--- | :--- | :--- |
| `tryon_jobs_created_total` | Counter | `category`, `env` | Ingress job demand volume |
| `tryon_jobs_completed_total` | Counter | `category`, `provider`, `env` | Successful try-on generation |
| `tryon_jobs_failed_total` | Counter | `error_class`, `provider`, `env` | Failed try-on volume |
| `tryon_job_duration_seconds` | Histogram | `status`, `env` | End-to-end customer-perceived latency |
| `tryon_provider_duration_seconds`| Histogram | `provider`, `model_version` | Upstream provider latency |
| `tryon_provider_attempts_total` | Counter | `provider`, `http_status` | Upstream invocation volume |
| `tryon_submission_unknown_total` | Counter | `provider`, `env` | Ambiguous network timeouts post-submit |
| `tryon_retry_total` | Counter | `error_class`, `retry_number` | Transient failure retry volume |
| `tryon_dead_letters_open` | Gauge | `queue`, `env` | Unresolved dead letter backlog |
| `tryon_result_storage_failures` | Counter | `bucket`, `error_class` | S3 persistence failures |
| `tryon_cache_hits_total` | Counter | `category`, `env` | Cache hit count (cost savings) |
| `tryon_cache_misses_total` | Counter | `category`, `env` | Cache miss count |
| `tryon_estimated_cost_total` | Counter | `provider`, `env` | Real-time estimated spend ($ USD) |
| `tryon_reconciled_cost_total` | Counter | `provider`, `env` | Reconciled invoice spend ($ USD) |
| `tryon_feedback_reports_total` | Counter | `reason_code`, `category` | Shopper quality complaints |

> [!IMPORTANT]
> Never include user IDs, email addresses, job IDs, or presigned URLs as Prometheus metric label values.

---

## 2. Alert Definitions & Thresholds

| Alert Identifier | Severity | Trigger Condition | Immediate Impact | Action Required |
| :--- | :--- | :--- | :--- | :--- |
| `TryOnProviderAuthFailure` | **P0 Critical** | 3 consecutive 401/403 responses | All live inference blocked | Verify & rotate API keys in AWS Secrets Manager |
| `TryOnGlobalBudgetExceeded` | **P0 Critical** | Monthly spend reaches 95% of cap | Approaching hard budget limit | Review spend velocity; invoke kill switch if unauthorized |
| `TryOnProviderDegraded` | **P1 High** | 5xx error rate > 15% over 5m | Customer latency / failures | Check provider status page; trip circuit breaker |
| `TryOnStuckLeasesDetected` | **P1 High** | > 5 jobs with lease expired > 300s | Stuck worker processes | Run stuck lease recovery sweeper; restart workers |
| `TryOnDeadLetterSpike` | **P2 Medium** | > 10 dead letters in 1 hour | Repeated unrecoverable failures| Inspect DLQ safe payload; investigate root cause |
| `TryOnQualityReportSpike` | **P2 Medium** | > 10 feedback reports for category | Possible model regression | Audit category quality; disable category if distorted |

---

## 3. Incident Runbook Procedures (15 Standard Procedures)

### Procedure 1: Emergency Kill Switch (Disable Paid Submissions)
When unexpected costs or severe provider corruption occurs:
1. Set server configuration: `VTO_GLOBAL_KILL_SWITCH = true`.
2. Existing jobs in progress complete; all new `POST /tryon/jobs` requests fast-fail with HTTP 503 Service Unavailable.
3. Status retrieval (`GET /tryon/jobs/{id}`) and feedback submissions remain fully functional.

### Procedure 2: Inspect Provider Health and Credentials
1. Query AWS Secrets Manager for secret freshness.
2. Verify connectivity from worker VPC to provider endpoint (`https://api.fashn.ai/v1/`).
3. Confirm account balance and active tier on provider console.

### Procedure 3: Inspect Stuck Jobs
Identify jobs stuck in `PROCESSING` longer than 600s:
```sql
SELECT job_id, user_id, status, lease_owner, lease_expires_at, created_at 
FROM tryon_jobs 
WHERE status = 'PROCESSING' AND lease_expires_at < NOW() - INTERVAL '5 minutes';
```

### Procedure 4: Reconcile Ambiguous Submissions (`SUBMISSION_UNKNOWN`)
1. Filter jobs in state `SUBMISSION_UNKNOWN`.
2. Do NOT replay or re-enqueue automatically.
3. Query provider API using persisted `provider_request_id` to determine whether generation succeeded or failed upstream.
4. If completed, download output and complete job; if failed, mark `FAILED`.

### Procedure 5: Recover Expired Worker Leases
Execute worker lease sweep:
```bash
python -m fashx.workers.sweepers.lease_recovery --max-jobs 50
```
Leases expired $> 300\text{s}$ are released back to `QUEUED` if attempt count $< 3$.

### Procedure 6: Inspect Dead-Letter Queue (DLQ)
```sql
SELECT dead_letter_id, task_id, task_name, error_type, attempts, created_at 
FROM tryon_dead_letters 
ORDER BY created_at DESC LIMIT 20;
```

### Procedure 7: Retry Safe Failures
Safe failures (transient timeouts where no provider attempt record exists) can be retried:
```bash
python -m fashx.workers.sweepers.dlq_retry --task-id <TASK_UUID>
```

### Procedure 8: Avoid Replaying Paid Ambiguous Submissions
- **Rule**: If a job has a recorded `provider_request_id`, it must NEVER be submitted as a new inference request.
- Use provider status polling only to resolve completion.

### Procedure 9: Reconcile Provider Billing
1. Export monthly ledger:
   ```sql
   SELECT provider, SUM(estimated_cost_usd) AS total_est, COUNT(*) AS invocations 
   FROM tryon_usage_ledger 
   WHERE created_at >= '2026-11-01' GROUP BY provider;
   ```
2. Reconcile against provider invoice statement.
3. Update `reconciled_cost_usd` via billing reconciliation migration.

### Procedure 10: Disable an Unreliable VTO Category
If a category exhibits visual distortion:
1. Update `CATEGORY_GATES` in `backend/fashx/tryon/evaluation/category_gates.py` or set environment feature flag `VTO_BLOCKED_CATEGORIES="sarees,lehengas,dresses"`.
2. Validation immediately fails closed for those categories.

### Procedure 11: Suspend a Merchant Catalog Source
If a merchant requests immediate takedown:
1. Update merchant status to `SUSPENDED` in catalog database.
2. Invalidate all active try-on cache keys referencing the merchant ID.
3. Time-of-Use guard halts any currently queued jobs for that merchant.

### Procedure 12: Invalidate Affected Cache Entries
```bash
python -m fashx.tryon.cache.invalidation --garment-id <GARMENT_UUID>
```
Purges Redis key references and associated presigned URLs.

### Procedure 13: Handle Shopper Image Deletion
Upon user account or photo deletion:
1. Delete portrait from private S3 bucket.
2. Purge user cache keys: `python -m fashx.tryon.cache.invalidation --user-id <USER_UUID>`.
3. Anonymize past completed job records in compliance with retention policy.

### Procedure 14: Handle Provider Outage
1. When upstream 503 rate exceeds 20%, trip circuit breaker.
2. New requests return friendly error message ("Virtual try-on temporarily unavailable; size charts available").
3. Background polling continues on previously submitted jobs.

### Procedure 15: Restore Service and Verify with Bounded Request
1. Untrip circuit breaker or disable kill switch.
2. Run single bounded test:
   ```bash
   python scripts/ops/run_bounded_live_tryon_test.py --environment staging --max-requests 1
   ```
3. Confirm end-to-end completion, S3 persistence, and ledger logging before restoring full customer traffic.
