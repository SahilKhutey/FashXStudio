import logging
from contextvars import ContextVar
from uuid import uuid4

from .settings import get_settings

_request_id: ContextVar[str] = ContextVar("request_id", default="")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_request_id() -> str:
    return _request_id.get()


def get_trace_id() -> str:
    return _trace_id.get()


def set_request_context(request_id: str | None = None, trace_id: str | None = None) -> tuple[str, str]:
    req = request_id or str(uuid4())
    trace = trace_id or str(uuid4())
    _request_id.set(req)
    _trace_id.set(trace)
    return req, trace


def clear_request_context() -> None:
    _request_id.set("")
    _trace_id.set("")


def configure_sentry() -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.app_version,
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        send_default_pii=False,
    )


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.trace_id = get_trace_id()
        return True
