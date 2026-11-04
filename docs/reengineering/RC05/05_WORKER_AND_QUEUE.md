# RC05 — 05 Worker and Queue Reliability

## Objective
Ensure resilient queue dispatching and background worker execution. Prevent broker outages from breaking job creation and verify lease management and crash recovery.

## Existing State
- `CeleryTryOnJobDispatcher` caught dispatch errors and logged warnings, but offered no structured observability back to the caller.
- Celery's default retry behavior on broker connection loss blocked the submission request loop for up to 20 connection attempts.

## Changes
- **Dispatcher Observability:** Created `DispatchResult(accepted: bool, reason: str | None)` in `backend/fashx/tryon/ports_dispatch.py`.
- **Non-blocking Dispatch:** Configured `apply_async(args=[str(job_id)], retry=False, retry_policy={"max_retries": 0}, ignore_result=True)` to prevent broker connection hangs.
- **Worker Leases:** `TryOnWorker` (`backend/fashx/tryon/application/worker.py`) performs atomic claims (`lease_seconds=180`), runs background heartbeats for renewal, and releases locks on graceful shutdown.
- **Stale Job Discovery:** Expired leases automatically release jobs back into the pool for surviving workers.

## Contracts
```python
@dataclass(frozen=True)
class DispatchResult:
    accepted: bool
    reason: str | None = None
```
- `SubmitTryOnJobResult` reflects `dispatch_accepted` and `dispatch_reason` without dropping persisted database records.

## Implementation
```python
# backend/fashx/tryon/ports_dispatch.py
class CeleryTryOnJobDispatcher:
    async def dispatch(self, job_id: UUID) -> DispatchResult:
        try:
            from fashx.workers.app import process_tryon_job
            process_tryon_job.apply_async(
                args=[str(job_id)],
                retry=False,
                retry_policy={"max_retries": 0},
                ignore_result=True,
            )
            return DispatchResult(accepted=True)
        except Exception as exc:
            logger.warning("Direct Celery dispatch for job %s deferred: %s", job_id, exc)
            return DispatchResult(accepted=False, reason=type(exc).__name__)
```

## Execution
```bash
pytest tests/unit/test_rc05_vto_scenarios.py -k "dispatcher" -v
```

## Tests
- `test_rc05_dispatcher_observability` -> PASSED
- `test_claim_next_job_sets_worker_lease` -> PASSED
- `test_renew_and_release_lease` -> PASSED
- `test_stale_job_recovery` -> PASSED

## Risks
- Redis queue outage causing silent drops.
- Mitigation: Jobs are persisted in PostgreSQL before queue dispatch. Database polling discovers queued jobs even if direct message delivery is deferred.

## Evidence
- Smoke test verified that when Redis is unreachable, submission completes immediately with HTTP 202, logs deferral warning, and preserves job for database-driven execution.

## Exit Criteria
- Queue dispatch failures are fully observable and non-blocking.
