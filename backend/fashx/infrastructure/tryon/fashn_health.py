"""FASHN API Health Check and Structured Audit Logging Module.

Provides pre-flight connectivity verification and privacy-safe operational
audit logging for virtual try-on provider requests.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx

log = logging.getLogger("fashx.tryon.provider.fashn")

# Fields to sanitize or scrub from logs
SENSITIVE_FIELD_SUBSTRINGS = {"key", "secret", "token", "auth", "image", "bytes", "photo"}


def _sanitize_log_data(data: dict[str, Any]) -> dict[str, Any]:
    """Scrub raw binary data, base64 strings, and credentials from log dictionaries."""
    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        k_lower = k.lower()
        if any(sub in k_lower for sub in SENSITIVE_FIELD_SUBSTRINGS):
            if "key" in k_lower or "secret" in k_lower or "token" in k_lower or "auth" in k_lower:
                sanitized[k] = "[REDACTED]"
            elif "image" in k_lower or "bytes" in k_lower or "photo" in k_lower:
                if isinstance(v, (bytes, bytearray)):
                    sanitized[k] = f"<{len(v)} bytes>"
                elif isinstance(v, str) and (v.startswith("data:") or len(v) > 256):
                    sanitized[k] = f"<{len(v)} chars (data/b64)>"
                else:
                    sanitized[k] = v
            else:
                sanitized[k] = "[REDACTED]"
        elif isinstance(v, str) and (v.startswith("data:") or len(v) > 512):
            sanitized[k] = f"<{len(v)} chars>"
        elif isinstance(v, (bytes, bytearray)):
            sanitized[k] = f"<{len(v)} bytes>"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_log_data(v)
        else:
            sanitized[k] = v
    return sanitized


def log_provider_event(
    event_name: str,
    details: dict[str, Any],
    level: int = logging.INFO,
) -> None:
    """Emit a structured, privacy-safe JSON log event."""
    safe_details = _sanitize_log_data(details)
    payload = {
        "event": event_name,
        "timestamp_ns": time.time_ns(),
        **safe_details,
    }
    log.log(level, json.dumps(payload))


@dataclass(frozen=True)
class FashnHealthReport:
    """Result of provider connectivity and balance check."""

    status: str  # "HEALTHY", "DEGRADED", "UNHEALTHY", "UNAVAILABLE"
    healthy: bool
    provider: str = "fashn_api"
    model: str = "tryon-v1.6"
    credits_remaining: float | None = None
    latency_ms: float = 0.0
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_fashn_health(
    client: httpx.Client,
    model: str = "tryon-v1.6",
    *,
    timeout_s: float = 5.0,
) -> FashnHealthReport:
    """Perform pre-flight connectivity and balance probe against FASHN API."""
    t0 = time.monotonic()
    try:
        # FASHN API exposes /credits endpoint to query account credit balance
        r = client.get("/credits", timeout=timeout_s)
        latency_ms = round((time.monotonic() - t0) * 1000, 2)
    except httpx.TransportError as exc:
        latency_ms = round((time.monotonic() - t0) * 1000, 2)
        log_provider_event(
            "tryon.provider.health_check",
            {"status": "UNAVAILABLE", "error": type(exc).__name__, "latency_ms": latency_ms},
            level=logging.ERROR,
        )
        return FashnHealthReport(
            status="UNAVAILABLE",
            healthy=False,
            model=model,
            latency_ms=latency_ms,
            detail=f"Network transport error: {type(exc).__name__}",
        )

    if r.status_code == 200:
        credits_val: float | None = None
        try:
            body = r.json()
            if isinstance(body, dict):
                credits_raw = None
                for key in ("credits", "balance", "credits_remaining"):
                    if key in body and body[key] is not None:
                        credits_raw = body[key]
                        break
                if credits_raw is not None:
                    credits_val = float(credits_raw)
        except Exception:
            credits_val = None

        is_healthy = True if (credits_val is None or credits_val > 0) else False
        status = "HEALTHY" if is_healthy else "DEGRADED"
        detail = "Provider online and responsive" if is_healthy else "Provider balance exhausted (0 credits)"

        log_provider_event(
            "tryon.provider.health_check",
            {"status": status, "credits_remaining": credits_val, "latency_ms": latency_ms},
            level=logging.INFO if is_healthy else logging.WARNING,
        )
        return FashnHealthReport(
            status=status,
            healthy=is_healthy,
            model=model,
            credits_remaining=credits_val,
            latency_ms=latency_ms,
            detail=detail,
        )

    if r.status_code in (401, 403):
        log_provider_event(
            "tryon.provider.health_check",
            {"status": "UNHEALTHY", "http_status": r.status_code, "latency_ms": latency_ms},
            level=logging.ERROR,
        )
        return FashnHealthReport(
            status="UNHEALTHY",
            healthy=False,
            model=model,
            latency_ms=latency_ms,
            detail="Authentication failed: invalid or revoked FASHN_API_KEY",
        )

    if r.status_code == 402:
        log_provider_event(
            "tryon.provider.health_check",
            {"status": "DEGRADED", "http_status": 402, "latency_ms": latency_ms},
            level=logging.ERROR,
        )
        return FashnHealthReport(
            status="DEGRADED",
            healthy=False,
            model=model,
            credits_remaining=0.0,
            latency_ms=latency_ms,
            detail="FASHN subscription or credit balance exhausted",
        )

    log_provider_event(
        "tryon.provider.health_check",
        {"status": "DEGRADED", "http_status": r.status_code, "latency_ms": latency_ms},
        level=logging.WARNING,
    )
    return FashnHealthReport(
        status="DEGRADED",
        healthy=False,
        model=model,
        latency_ms=latency_ms,
        detail=f"Unexpected provider status: HTTP {r.status_code}",
    )
