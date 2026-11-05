# RC05 — 06 Provider Execution

## Objective
Govern the execution flow for third-party hosted VTO providers (FASHN API) and development adapters, ensuring that provider job IDs are persisted prior to status polling to guarantee crash recovery without duplicate inference requests.

## Existing State
- Two-phase provider pattern (`submit` followed by `collect`).
- `provider_job_id` stored in database.

## Changes
- Verified that `provider_job_id` is written to `TryOnJob` and committed before entering the polling phase (`adapter.collect()`).
- In `ProcessTryOnJobUseCase`, checked `if not provider_job_id:` before calling `adapter.submit(req)`:
  - If a worker crashes while polling and restarts, it detects the existing `provider_job_id` and resumes collection directly.
- Mapped error codes:
  - Fatal: `provider_auth`, `unsupported_garment`, `quality_rejected` -> mark job failed.
  - Retryable: `provider_unavailable`, `provider_timeout`, `breaker_open` -> requeue with exponential backoff.

## Contracts
- Provider job submission payload (`TryOnRequest`):
  - `person_jpeg`: Normalized JPEG image bytes
  - `garment_jpeg`: Normalized JPEG image bytes
  - `category`: `tops` | `bottoms` | `one-pieces` | `auto`
- Return value: `TryOnOutput`:
  - `image_bytes`: Rendered result
  - `provider`: Provider identifier (`fashn_api` or `mock`)
  - `model`: Model version string
  - `provider_job_id`: Remote job identifier
  - `latency_ms`: Execution time
  - `cost_usd_est`: Estimated provider cost

## Implementation
```python
# backend/fashx/tryon/application/process_job.py
provider_job_id = getattr(job, "provider_job_id", None)
if not provider_job_id:
    # 1. Submit to provider
    provider_job_id = await asyncio.to_thread(self.adapter.submit, req)
    # 2. Persist before polling
    async with self.tryon_uow:
        await self.tryon_uow.jobs.set_provider_job(job.id, provider_name, provider_job_id)
        job.provider_job_id = provider_job_id
        await self.tryon_uow.commit()

# 3. Collect status
out = await asyncio.to_thread(self.adapter.collect, provider_job_id, deadline_s=deadline_s)
```

## Execution
```bash
pytest tests/unit/test_rc05_vto_scenarios.py -k "resume_collection" -v
```

## Tests
- `test_rc05_t09_t10_resume_collection_with_persisted_provider_job` -> PASSED
- `test_fashn_api_submit_collect_mock_transport` -> PASSED
- `test_fashn_api_error_mappings_and_ssrf_guard` -> PASSED

## Risks
- Double billing if worker restarts and submits new request.
- Mitigation: Tested assertion in `test_rc05_t09_t10` proves `submit()` is bypassed when `provider_job_id` is present.

## Evidence
```
test_rc05_t09_t10_resume_collection_with_persisted_provider_job PASSED
```

## Exit Criteria
- Provider interactions are resilient against network interruptions and worker process restarts.
