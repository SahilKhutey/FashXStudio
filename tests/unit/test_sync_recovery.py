"""Unit tests for bounded retry with exponential backoff and transient error recovery."""

import pytest

from fashx.catalog.acquisition.retry import retry_transient


@pytest.mark.asyncio
async def test_retry_transient_succeeds_first_attempt() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        return "success"

    res = await retry_transient(op, max_attempts=3, base_delay_seconds=0.01)
    assert res == "success"
    assert calls == 1


@pytest.mark.asyncio
async def test_retry_transient_recovers_after_temporary_failure() -> None:
    calls = 0

    async def flaky_op() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("Temporary network blip")
        return "recovered"

    res = await retry_transient(flaky_op, max_attempts=4, base_delay_seconds=0.01)
    assert res == "recovered"
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_transient_exhausts_and_raises() -> None:
    calls = 0

    async def always_failing() -> None:
        nonlocal calls
        calls += 1
        raise ConnectionError("Persistent network outage")

    with pytest.raises(ConnectionError, match="Persistent network outage"):
        await retry_transient(always_failing, max_attempts=3, base_delay_seconds=0.01)

    assert calls == 3


@pytest.mark.asyncio
async def test_retry_transient_does_not_catch_non_retryable_errors() -> None:
    calls = 0

    async def bad_data_op() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("Malformed catalog data")

    with pytest.raises(ValueError, match="Malformed catalog data"):
        await retry_transient(bad_data_op, max_attempts=3, base_delay_seconds=0.01)

    assert calls == 1  # Should not retry invalid data!
