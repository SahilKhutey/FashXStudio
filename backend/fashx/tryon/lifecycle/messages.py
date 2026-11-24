"""VTO User-Facing Failure Messages and Client Presentation Contracts (Phase 07.5)."""

from __future__ import annotations

from typing import Any

from fashx.tryon.lifecycle.errors import ErrorCode, classify_error


def get_user_failure(error_code: ErrorCode | str) -> dict[str, str]:
    """Retrieve normalized, empathetic, and actionable user-facing error message."""
    definition = classify_error(error_code)
    return {
        "code": definition.code.value,
        "message": definition.user_message,
        "suggested_action": definition.suggested_action,
    }


def format_client_status_response(
    *,
    job_id: str,
    status: str,
    progress_stage: str | None = None,
    retry_scheduled: bool = False,
    retry_after_seconds: float | None = None,
    result_url: str | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Format canonical client status payload with failure details when appropriate."""
    res: dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "progress_stage": progress_stage or status,
        "retry_scheduled": retry_scheduled,
        "result_available": result_url is not None,
        "result_url": result_url,
    }

    if retry_after_seconds is not None and retry_after_seconds > 0:
        res["retry_after_seconds"] = int(retry_after_seconds)

    if error_code:
        res["failure"] = get_user_failure(error_code)

    return res
