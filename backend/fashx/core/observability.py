from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any
from uuid import uuid4

from .logging import scrub
from .settings import get_settings

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_request_id() -> str:
    return _request_id.get()


def get_trace_id() -> str:
    return _trace_id.get()


def set_request_context(
    request_id: str | None = None, trace_id: str | None = None
) -> tuple[str, str]:
    req = request_id or str(uuid4())
    trace = trace_id or str(uuid4())
    _request_id.set(req)
    _trace_id.set(trace)
    return req, trace


def clear_request_context() -> None:
    _request_id.set("")
    _trace_id.set("")


def _sentry_before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitize Sentry events before dispatch to ensure zero credentials or PII leak to Sentry."""
    if "request" in event:
        req = event["request"]
        # Scrub headers
        if "headers" in req:
            req["headers"] = scrub(req["headers"])
        # Strip URL query parameters if they contain S3 or token patterns
        if "url" in req:
            req["url"] = scrub(req["url"])
        # Strip sensitive request bodies
        if "data" in req:
            req["data"] = "[redacted]"

    # Scrub exception values
    if "exception" in event:
        for ex in event.get("exception", {}).get("values", []):
            if "value" in ex:
                ex["value"] = scrub(ex["value"])

    return event


def configure_sentry(settings: Any | None = None) -> None:
    if settings is None:
        settings = get_settings()
    if not getattr(settings, "sentry_dsn", None):
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=getattr(settings, "app_version", "0.2.0"),
        traces_sample_rate=0.1 if getattr(settings, "is_production", False) else 1.0,
        send_default_pii=False,
        before_send=_sentry_before_send,
    )


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.trace_id = get_trace_id()
        return True
