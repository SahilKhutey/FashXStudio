"""W3C Trace Context and distributed correlation utilities for FashXStudio."""

from __future__ import annotations

import re
import secrets

# Standard W3C traceparent regex: version-trace_id-parent_id-trace_flags
# Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
_TRACEPARENT_REGEX = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
)


def is_valid_traceparent(traceparent: str | None) -> bool:
    """Validate whether an inbound traceparent header conforms to the W3C Trace Context specification."""
    if not traceparent:
        return False
    match = _TRACEPARENT_REGEX.match(traceparent)
    if not match:
        return False
    trace_id, parent_id, _ = match.groups()
    # W3C spec forbids all-zero trace_id or parent_id
    if trace_id == "0" * 32 or parent_id == "0" * 16:
        return False
    return True


def generate_traceparent(sampled: bool = True) -> str:
    """Generate a valid W3C traceparent header."""
    trace_id = secrets.token_hex(16)  # 32 hex chars
    parent_id = secrets.token_hex(8)  # 16 hex chars
    flags = "01" if sampled else "00"
    return f"00-{trace_id}-{parent_id}-{flags}"


def parse_traceparent(traceparent: str | None) -> tuple[str, str, str] | None:
    """Parse traceparent into (trace_id, parent_id, flags) or None if invalid."""
    if not is_valid_traceparent(traceparent):
        return None
    match = _TRACEPARENT_REGEX.match(traceparent)  # type: ignore[arg-type]
    if match:
        return match.groups()  # type: ignore[return-value]
    return None


def extract_trace_id(traceparent: str | None, fallback: str | None = None) -> str:
    """Extract the 32-character hex trace ID from traceparent, or return fallback/new trace ID."""
    parsed = parse_traceparent(traceparent)
    if parsed:
        return parsed[0]
    return fallback or secrets.token_hex(16)
