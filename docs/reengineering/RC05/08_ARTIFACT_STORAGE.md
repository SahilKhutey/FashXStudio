# RC05 — 08 Artifact Storage and Secure Delivery

## Objective
Implement and verify private, user-isolated object storage for virtual try-on artifacts. Ensure that access is controlled via expiring signed URLs and that cross-user access attempts are strictly rejected.

## Existing State
- Artifacts stored under structured object storage keys.
- Signed URL generation implemented with configurable expiration TTL.

## Changes
- Storage key standardized: `u/{user_id}/tryon/{job_id}.png`.
- Verified owner isolation in:
  - `GET /api/v1/tryon/jobs/{job_id}`: Returns 404 EntityNotFoundError if requester is not the job owner.
  - `GET /api/v1/tryon/artifacts/{artifact_key}`: Returns 403 Forbidden if requester is not the artifact owner.
- Signed URLs configured with 300-second (5-minute) TTL on status endpoints and 3600-second (1-hour) TTL on list endpoints.

## Contracts
- Artifact Response:
  ```json
  {
    "artifact_key": "d1f8a54bdca4050ef8b879265a3465d68690c9a2678df32f49875d9dfb90af0b",
    "result_key": "u/709a608d-1bfb-4e0e-8b0f-abfe0e40f97e/tryon/eb62d57a-35ee-4426-a08f-6e87de7d847b.png",
    "model_version": "mock-vto-v1",
    "pipeline_version": "pilot-pipe-v1",
    "photo_version": 1,
    "garment_version": 1,
    "quality_reasons": []
  }
  ```

## Implementation
```python
# backend/fashx/tryon/router.py
if str(job.user_id) != principal.user_id:
    raise forbidden("Forbidden: You cannot access this try-on result")

# Expiration URL generation
result_url = storage.signed_get_url(res.result_url, ttl_s=300)
```

## Execution
```bash
pytest tests/unit/test_rc05_vto_scenarios.py -k "owner_isolation" -v
```

## Tests
- `test_rc05_t13_owner_isolation_in_status_and_artifacts` -> PASSED
- `test_vto_phase6_artifacts.py` -> 27/27 PASSED

## Risks
- Storage keys leaked in client-side logs or public feeds.
- Mitigation: Raw storage keys are never public; only short-lived signed URLs scoped to authenticated requests are returned.

## Evidence
- Smoke test Step 6: User B accessing User A job -> HTTP 404; User B accessing User A artifact -> HTTP 403.

## Exit Criteria
- Private artifact storage enforced with zero cross-tenant leakage.
