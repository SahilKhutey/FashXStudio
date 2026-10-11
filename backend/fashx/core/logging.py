import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

_PATTERNS = [
    re.compile(r"eyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}"),  # JWT tokens
    re.compile(r"X-Amz-(Signature|Credential|Security-Token)=[^&\s\"']+", re.I),  # presigned URL parts
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # Email addresses
    re.compile(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]{20,}"),  # Inline images
    re.compile(r"[A-Za-z0-9+/]{200,}={0,2}"),  # Long base64 / blob strings
]


def scrub(v: Any) -> Any:
    """Recursively redact PII, credentials, tokens, and payloads from logged structures."""
    if isinstance(v, str):
        res = v
        for p in _PATTERNS:
            res = p.sub("[redacted]", res)
        return res
    if isinstance(v, dict):
        return {
            k: (
                "[redacted]"
                if k.lower() in {"authorization", "token", "password", "secret", "api_key", "bearer"}
                else scrub(x)
            )
            for k, x in v.items()
        }
    if isinstance(v, (list, tuple)):
        return type(v)(scrub(x) for x in v)
    return v


class RedactFilter(logging.Filter):
    """Filter applied to the root logger so no code path leaks personal data or credentials."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(record.getMessage())
        record.args = ()
        for k, v in list(getattr(record, "__dict__", {}).items()):
            if k not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__ and k != "msg":
                setattr(record, k, scrub(v))
        return True


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter outputting one JSON object per line for CloudWatch Logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.msg,
        }

        # Include structured context fields if present
        context_keys = (
            "request_id",
            "user_id",
            "route_template",
            "method",
            "status",
            "latency",
            "per_stage_timings",
            "ranker_version",
            "job_id",
            "vendor_job_id",
            "error_code",
            "app_version",
            "trace_id",
            "pd_access",
        )
        for key in context_keys:
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = scrub(val)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def log_pd_access(actor: str, user_id: str, action: str, purpose: str) -> None:
    """Emit a structured pd_access audit log entry (DPDP / CERT-In compliance)."""
    audit_logger = logging.getLogger("fashx.audit.pd_access")
    audit_logger.info(
        f"personal_data_access: {action} on {user_id}",
        extra={
            "user_id": str(user_id),
            "pd_access": {
                "actor": actor,
                "user_id": str(user_id),
                "action": action,
                "purpose": purpose,
                "time": datetime.now(UTC).isoformat(),
            },
        },
    )


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with RedactFilter and structured JsonFormatter."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactFilter())
    root.handlers.clear()
    root.addHandler(handler)
