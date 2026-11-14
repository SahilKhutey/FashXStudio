# Incident Response Runbook & Troubleshooting Guide

## 1. Incident Lifecycle & Severity Protocol

This runbook guides on-call engineers through responding to CloudWatch alarms, system degradation, or customer-reported outages in FashXStudio production.

```mermaid
flowchart LR
    A[1. Alarm Triggers via SNS] --> B[2. Acknowledge & Triage]
    B --> C[3. Mitigate & Stabilize]
    C --> D[4. Root Cause Analysis]
    D --> E[5. Resolve & Clear Alarm]
    E --> F[6. Post-Incident Review]
```

### Escalation Timeline
- **P1 (Critical)**: Acknowledge within 15 minutes. Notify founder and engineering lead. Post incident channel status updates every 30 minutes.
- **P2 (High)**: Acknowledge within 60 minutes. Update status every 2 hours.

---

## 2. Scenario Runbooks

### Runbook 1: API 5xx Error Surge (`API-5xx-Rate-High-Production`)

**Symptom**: CloudWatch Alarm fires; `Api5xxErrors > 10` in a 2-minute window.

**Step-by-step Triage**:
1. **Check Sentry**: Open Sentry Dashboard (filtered by `environment: prod`) to view the unhandled exception stack trace and affected route.
2. **Inspect CloudWatch Logs Insights**:
   ```sql
   fields @timestamp, route, status_code, message, request_id
   | filter status_code >= 500
   | stats count(*) by message, route
   ```
3. **Assess Recent Deployments**:
   - Check if a new ECS task definition was registered in the last 30 minutes.
   - If error surge immediately followed a deployment, trigger immediate rollback:
     ```bash
     bash scripts/release/rollback_ecs.sh fashx-prod api
     ```
4. **Verify Core Dependencies**:
   - Query `/healthz/ready` to verify PostgreSQL and Redis connectivity.
   - If database or cache connection fails, proceed to Runbook 3 or Runbook 4.

---

### Runbook 2: Celery Worker Outage or Backlog (`Queue-Depth-High-Production`)

**Symptom**: `QueueDepth` on `vto` queue exceeds 50 tasks for > 5 minutes, or `WorkerHeartbeat` is missing.

**Step-by-step Triage**:
1. **Check Worker ECS Task Status**:
   ```bash
   aws ecs describe-services --cluster fashx-prod --services fashx-prod-worker
   ```
   - Verify `runningCount` equals `desiredCount`.
   - If tasks are crashing in a restart loop (`CrashLoop`), inspect container exit codes and logs in CloudWatch log group `/fashx/prod/worker`.
2. **Check for Unacknowledged Task Deadlocks**:
   - Inspect whether long-running tasks are exceeding timeouts (90s limit on VTO inference).
3. **Temporarily Scale Worker Concurrency**:
   - If queue depth is climbing due to legitimate traffic burst, scale up worker tasks:
     ```bash
     aws ecs update-service --cluster fashx-prod --service fashx-prod-worker --desired-count 6
     ```
4. **Inspect Dead-Letter Queue**:
   - If `Dead-Letter-Queue-Non-Zero-Production` triggered, inspect messages routed to `dead_letter` queue to identify unhandled malformed payloads.

---

### Runbook 3: Database Connection Pool Exhaustion (`DB-Connection-Pool-Exhaustion-Production`)

**Symptom**: `DbPoolCheckedOut` approaches maximum limit; API requests begin failing with connection pool timeout errors.

**Step-by-step Triage**:
1. **Query Active Database Connections**:
   Connect to PostgreSQL via read-replica or maintenance bastion and check active queries:
   ```sql
   SELECT pid, now() - query_start AS duration, state, query
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC
   LIMIT 10;
   ```
2. **Terminate Hanging or Idle Transactions**:
   If orphan transactions are holding locks or idle in transaction:
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
     AND now() - query_start > interval '2 minutes';
   ```
3. **Check for Slow Table Scans or Missing Indexes**:
   - Inspect query plans for recent slow routes in CloudWatch Logs.

---

### Runbook 4: VTO Provider Rate Limiting or Outage (`VTO-Provider-Rate-Limit-Production`)

**Symptom**: `VTOProviderRateLimit` (429) > 3 or `VTOProviderAuthFailure` (401) > 0.

**Step-by-step Triage**:
1. **For HTTP 401 Auth Failure**:
   - Check FASHN API account portal for billing threshold or credit exhaustion.
   - Verify that `FASHN_API_KEY` in AWS Secrets Manager has not expired or been revoked.
2. **For HTTP 429 Rate Limiting**:
   - Throttle the Celery worker concurrency for the `vto` queue:
     ```bash
     aws ecs update-service --cluster fashx-prod --service fashx-prod-worker --desired-count 2
     ```
   - Check if automated testing or runaway client loop is flooding the submission endpoint.
3. **Notify Users if Provider Outage**:
   - If upstream status page reports an active outage, toggle maintenance mode or display a user-friendly degraded status message on the try-on client interface.

---

### Runbook 5: S3 Erasure or Storage Failure (`S3-Storage-Errors-Production`)

**Symptom**: Non-zero `StorageDeleteError` or high `StorageUploadError`.

**Step-by-step Triage**:
1. **Inspect CloudWatch Logs for S3 Error Codes**:
   - Look for `AccessDenied`, `NoSuchBucket`, or `EndpointConnectionError`.
2. **Verify ECS Task IAM Roles**:
   - Verify that the ECS task role has `s3:PutObject`, `s3:GetObject`, and `s3:DeleteObject` permissions on `fashx-prod-private-*`.
3. **Retry Failed User Erasures**:
   - For GDPR / data privacy compliance, identify failed delete requests and re-queue erasure jobs manually once permissions or endpoint connectivity is restored.

---

## 3. Post-Incident Review (PIR) Checklist

Within 48 hours of resolving any P1 incident:
- [ ] Record incident timeline and duration in `docs/incidents/`.
- [ ] Quantify customer impact (failed try-on attempts, affected user sessions).
- [ ] Identify root cause and contributing environmental factors.
- [ ] Create preventive engineering tickets (e.g. timeout tuning, index additions, retry adjustments).
- [ ] Verify that alarm thresholds and runbook steps accurately reflected the failure mode.
