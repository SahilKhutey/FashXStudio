# RC05 — 11 Privacy and Resilience

## Objective
Enforce strict privacy guarantees across portrait and try-on artifact processing, including in-flight consent revocation, account erasure, and failure recovery.

## Existing State
- Multi-point consent checks implemented in `SubmitTryOnJobUseCase` and `ProcessTryOnJobUseCase`.
- Erasure sweep tasks registered in `fashx.workers.app`.

## Changes
- **Mid-Flight Revocation Verification:**
  - If `body_photo` consent is revoked while a job is in the queue, worker execution cancels the job with `failure_reason="consent_revoked"`.
  - If consent is revoked during provider inference, post-inference checks catch the revocation before saving the artifact, deleting any temporary bytes and marking the job `cancelled`.
  - If consent is revoked between storage upload and database commit, the uploaded artifact in storage is explicitly deleted (`storage.delete(key)`).
- **Tenant Isolation:** Cross-user job querying, artifact fetching, and feedback submission are strictly blocked with 403 or 404 responses.
- **Worker Crash Resilience:** If a worker restarts with an active `provider_job_id`, it skips `submit` and collects results directly.

## Privacy Checkpoints in Pipeline
```
[User Request]
       │
       ▼
1. Pre-Submission Consent Check: body_photo must be active (submit_job.py:61)
       │
       ▼
2. Worker Claim & Start Check: body_photo must be active (process_job.py:105)
       │
       ▼
3. Pre-Inference Revalidation Check: body_photo must be active (process_job.py:330)
       │
       ▼
4. Post-Inference Revalidation Check: body_photo must be active (process_job.py:480)
       │
       ▼
5. Post-Storage Upload Check: body_photo must be active (process_job.py:601)
   └─ If revoked: delete uploaded key from bucket, cancel job, abort DB commit
       │
       ▼
[Completed Artifact Published]
```

## Contracts
- Revoked consent: Job status becomes `cancelled`, failure reason `consent_revoked`.
- Cross-user job status: HTTP 404 EntityNotFoundError.
- Cross-user artifact key: HTTP 403 Forbidden.

## Implementation
- Documented in `backend/fashx/tryon/application/process_job.py` lines 104-118, 329-345, 478-494, 599-605, 646-655.

## Execution
```bash
pytest tests/unit/test_rc05_vto_scenarios.py -k "consent_revocation or owner_isolation" -v
```

## Tests
- `test_rc05_t14_t15_consent_revocation_cancels_job` -> PASSED
- `test_rc05_t13_owner_isolation_in_status_and_artifacts` -> PASSED

## Risks
- Dangling images remaining in object storage after consent withdrawal.
- Mitigation: Post-upload check immediately invokes `storage.delete(key)` upon detecting consent changes.

## Evidence
- Automated tests pass; smoke test step 6 verified cross-tenant blocking.

## Exit Criteria
- In-flight and post-execution privacy and resilience guarantees strictly maintained.
