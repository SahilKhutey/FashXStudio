import pytest

from fashx.application.ports.tryon import TryOnError
from fashx.ml.breaker import InMemoryBreaker


def test_circuit_breaker_trips_at_threshold():
    cb = InMemoryBreaker(threshold=3, window_s=60, open_s=60)

    # Initial state: closed
    cb.guard()

    # Failures 1 and 2: still closed
    cb.failure()
    cb.guard()
    cb.failure()
    cb.guard()

    # Failure 3: trips open
    cb.failure()
    with pytest.raises(TryOnError) as exc:
        cb.guard()
    assert exc.value.code == "breaker_open"
    assert exc.value.retryable is True


def test_circuit_breaker_resets_on_success():
    cb = InMemoryBreaker(threshold=3, window_s=60, open_s=60)

    cb.failure()
    cb.failure()
    cb.success()

    # Failures count should reset
    cb.failure()
    cb.guard()  # Still not tripped
