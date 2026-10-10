"""Stage-level latency instrumentation and Server-Timing header generation."""

import contextvars
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

_CURRENT_STAGES: contextvars.ContextVar[dict[str, float] | None] = contextvars.ContextVar(
    "current_stages", default=None
)


def start_stage_recording() -> dict[str, float]:
    """Initialize a stage timing container for the current async task / context."""
    stages: dict[str, float] = {}
    _CURRENT_STAGES.set(stages)
    return stages


def get_current_stages() -> dict[str, float]:
    """Retrieve the current recorded stages dictionary, creating one if not present."""
    stages = _CURRENT_STAGES.get()
    if stages is None:
        stages = {}
        _CURRENT_STAGES.set(stages)
    return stages


@contextmanager
def stage(name: str) -> Generator[None, Any, None]:
    """Context manager measuring execution time of a pipeline stage in milliseconds.

    Example:
        with stage("retrieval"):
            candidates = query_candidates(...)
    """
    stages = get_current_stages()
    start_t = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        # If the stage is executed multiple times, accumulate or overwrite
        stages[name] = stages.get(name, 0.0) + elapsed_ms


def format_server_timing(stages: dict[str, float] | None = None) -> str:
    """Format recorded stage metrics into a W3C Server-Timing header string.

    Format: 'retrieval;dur=12.4, scoring;dur=8.1, mmr;dur=4.2'
    """
    if stages is None:
        stages = get_current_stages()

    parts = [f"{st_name};dur={dur_ms:.1f}" for st_name, dur_ms in stages.items()]
    return ", ".join(parts)
