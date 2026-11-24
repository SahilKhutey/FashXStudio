# Phase 07.5 — Job States and Failure Handling

## 1. Objective
Implement a durable and reliable Virtual Try-On (VTO) job state machine that supports safe retries, worker restart recovery, cancellation, stuck-job detection, dead-letter handling, and useful user-facing errors.

---

## 2. Scope
- Define all supported job states and provider attempt states.
- Enforce valid state transitions.
- Reject invalid and stale concurrent updates via optimistic locking (`version`).
- Classify retryable and non-retryable failures.
- Configure operation-specific retry limits and exponential backoff with jitter.
- Implement worker execution timeout, lease tokens, and heartbeats.
- Detect and recover stuck jobs across state-specific thresholds.
- Implement cancellation and cancellation race protection.
- Implement durable dead-letter records (`tryon_dead_letters`).
- Prevent duplicate provider charges, duplicate results, and duplicate queue deliveries.
- Recover jobs after worker or broker restarts from durable checkpoints.
- Provide clear, safe, and actionable shopper-facing failure messages.

---

## 3. Architecture Rules
1. **PostgreSQL is the durable source of truth**: Redis and Celery are execution infrastructure, not the only record of a job.
2. **State changes must be validated and concurrency-safe**: Optimistic versioning (`version = version + 1`) and conditional SQL updates prevent race conditions.
3. **State transitions must have append-only audit events**: Every state change writes to `tryon_job_events`.
4. **A worker must hold a valid lease to update a job**: Unowned or expired lease updates are rejected.
5. **Retry decisions must be operation-specific**: Polling, download, or upload retries do not re-submit billable provider inferences.
6. **Ambiguous provider submissions must never be blindly repeated**: `SUBMISSION_UNKNOWN` requires reconciliation.
7. **Provider polling and result downloads must resume from durable checkpoints**: Recovering workers do not re-run previous successful steps.
8. **Cancellation requests must not falsely claim that provider inference has stopped**: Acknowledge cancellation truthfully and safely discard results.
9. **Dead-letter records must be durable and replay must be controlled**: Operator investigation is required before replaying failed tasks.
10. **Every completed job must have a validated and persisted result**: Output images undergo SSRF and Pillow validation before final completion.
11. **Every failure must have a normalized internal code and safe user-facing message**: Raw exceptions and secrets are scrubbed from user responses.

---

## 4. Documentation Index
- [7.5.01-repository-audit.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.01-repository-audit.md)
- [7.5.02-job-state-definitions.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.02-job-state-definitions.md)
- [7.5.03-transition-matrix.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.03-transition-matrix.md)
- [7.5.04-state-machine-implementation.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.04-state-machine-implementation.md)
- [7.5.05-error-classification.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.05-error-classification.md)
- [7.5.06-retry-policy.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.06-retry-policy.md)
- [7.5.07-timeout-and-worker-leases.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.07-timeout-and-worker-leases.md)
- [7.5.08-stuck-job-recovery.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.08-stuck-job-recovery.md)
- [7.5.09-cancellation-workflow.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.09-cancellation-workflow.md)
- [7.5.10-dead-letter-handling.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.10-dead-letter-handling.md)
- [7.5.11-idempotency-and-duplicate-prevention.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.11-idempotency-and-duplicate-prevention.md)
- [7.5.12-worker-restart-recovery.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.12-worker-restart-recovery.md)
- [7.5.13-user-facing-failure-messages.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.13-user-facing-failure-messages.md)
- [7.5.14-database-migrations.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.14-database-migrations.md)
- [7.5.15-test-plan.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.15-test-plan.md)
- [7.5.16-test-execution-report.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.16-test-execution-report.md)
- [7.5.17-operational-runbook.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.17-operational-runbook.md)
- [7.5.18-security-and-reliability-review.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.18-security-and-reliability-review.md)
- [7.5.19-performance-and-recovery-report.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5.19-performance-and-recovery-report.md)
- [7.5-FINAL-ACCEPTANCE-REPORT.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-07/7.5-job-states-and-failure-handling/7.5-FINAL-ACCEPTANCE-REPORT.md)
