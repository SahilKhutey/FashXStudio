import pytest

from fashx.integration.retry import RetryPolicy


@pytest.mark.asyncio
async def test_retry_policy_immediate_success():
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.01)
    call_count = 0

    async def op():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await policy.execute(op)
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_policy_eventual_success():
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.01)
    call_count = 0

    async def op():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary network glitch")
        return "recovered"

    result = await policy.execute(op)
    assert result == "recovered"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_policy_exhaustion_raises():
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.01)
    call_count = 0

    async def op():
        nonlocal call_count
        call_count += 1
        raise ValueError("Persistent failure")

    with pytest.raises(ValueError) as exc_info:
        await policy.execute(op)

    assert "Persistent failure" in str(exc_info.value)
    assert call_count == 3
