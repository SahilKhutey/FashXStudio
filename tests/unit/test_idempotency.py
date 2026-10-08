import pytest

from fashx.core.errors import IdempotencyConflictError
from fashx.core.idempotency import IdempotencyManager, IdempotencyStatus


@pytest.mark.asyncio
async def test_idempotency_lifecycle() -> None:
    mgr = IdempotencyManager()
    key = "idem-req-123"
    payload_hash = "hash-abc"

    # 1. First claim succeeds
    claim1 = await mgr.claim(key, payload_hash)
    assert claim1.claimed is True
    assert claim1.cached_response is None

    # 2. In-flight claim with same key raises conflict
    with pytest.raises(IdempotencyConflictError) as exc_info:
        await mgr.claim(key, payload_hash)
    assert "in progress" in str(exc_info.value)

    # 3. Complete request with cached response
    response_payload = {"job_id": "job-999", "status": "queued"}
    await mgr.complete(key, status_code=201, response_data=response_payload)

    # 4. Subsequent claim with identical hash returns cached result
    claim2 = await mgr.claim(key, payload_hash)
    assert claim2.claimed is False
    assert claim2.cached_status_code == 201
    assert claim2.cached_response == response_payload

    # 5. Subsequent claim with different payload hash raises conflict
    with pytest.raises(IdempotencyConflictError) as exc_info2:
        await mgr.claim(key, "different-hash-xyz")
    assert "different parameters" in str(exc_info2.value)


@pytest.mark.asyncio
async def test_idempotency_failure_permits_retry() -> None:
    mgr = IdempotencyManager()
    key = "idem-fail-retry"
    payload_hash = "hash-123"

    claim1 = await mgr.claim(key, payload_hash)
    assert claim1.claimed is True

    # Mark failed
    await mgr.fail(key)
    record = mgr._records[key]
    assert record.status == IdempotencyStatus.FAILED

    # Re-claiming after failure should succeed
    claim2 = await mgr.claim(key, payload_hash)
    assert claim2.claimed is True
