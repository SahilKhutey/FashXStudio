"""RC10 execution timing and synchronous profiling utility."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class TimingResult:
    """Stores the execution output and wall-clock duration in milliseconds."""
    value: Any
    duration_ms: float


def measure_call[T](fn: Callable[[], T]) -> tuple[T, TimingResult]:
    """Measure duration of a synchronous callable in milliseconds.

    Returns a tuple of (result_value, TimingResult(value, duration_ms)).
    Exceptions are propagated without modification.
    """
    started = perf_counter()
    value = fn()
    duration = (perf_counter() - started) * 1000.0
    return value, TimingResult(
        value=value,
        duration_ms=duration,
    )
