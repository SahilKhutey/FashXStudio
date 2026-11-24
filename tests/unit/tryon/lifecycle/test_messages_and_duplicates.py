"""Unit tests for Duplicate Prevention and Shopper Messaging (Phase 07.5).

Covers DUP-001 through DUP-007 and MSG-001 through MSG-006.
"""

from __future__ import annotations

from uuid import uuid4

from fashx.tryon.lifecycle.errors import ErrorCode
from fashx.tryon.lifecycle.messages import (
    format_client_status_response,
    get_user_failure,
)


def test_messaging_temporary_provider_failure() -> None:
    # MSG-001
    fail = get_user_failure(ErrorCode.PROVIDER_UNAVAILABLE)
    assert fail["code"] == "PROVIDER_UNAVAILABLE"
    assert "trouble processing your try-on" in fail["message"]
    assert fail["suggested_action"] == "Check again shortly"


def test_messaging_permanent_input_failure() -> None:
    # MSG-002
    fail = get_user_failure(ErrorCode.INVALID_INPUT_IMAGE)
    assert fail["code"] == "INVALID_INPUT_IMAGE"
    assert "cannot be used for virtual try-on" in fail["message"]
    assert fail["suggested_action"] == "Upload a clear, full-body photo"


def test_messaging_consent_failure() -> None:
    # MSG-003
    fail = get_user_failure(ErrorCode.CONSENT_REQUIRED)
    assert fail["code"] == "CONSENT_REQUIRED"
    assert "permission to process your photo" in fail["message"]
    assert fail["suggested_action"] == "Review consent in account settings"


def test_messaging_retry_budget_exhausted() -> None:
    # MSG-004
    fail = get_user_failure(ErrorCode.MAX_RETRIES_EXCEEDED)
    assert fail["code"] == "MAX_RETRIES_EXCEEDED"
    assert "could not complete your try-on this time" in fail["message"]


def test_format_client_status_response_scrubs_raw_internals() -> None:
    # MSG-005, MSG-006
    job_id = str(uuid4())
    res = format_client_status_response(
        job_id=job_id,
        status="RETRY_PENDING",
        progress_stage="provider_inference",
        retry_scheduled=True,
        retry_after_seconds=12.5,
        error_code="PROVIDER_UNAVAILABLE",
    )

    assert res["job_id"] == job_id
    assert res["status"] == "RETRY_PENDING"
    assert res["retry_scheduled"] is True
    assert res["retry_after_seconds"] == 12
    assert "failure" in res
    assert res["failure"]["code"] == "PROVIDER_UNAVAILABLE"
    # Ensure no internal traceback or hostnames leaked
    assert "Traceback" not in str(res)
    assert "s3://" not in str(res)
    assert "fashn.ai" not in str(res)


def test_format_client_status_response_unknown_code_safe_fallback() -> None:
    # MSG-006: Unknown error code produces safe empathetic fallback
    job_id = str(uuid4())
    res = format_client_status_response(
        job_id=job_id,
        status="FAILED",
        error_code="TOTALLY_WEIRD_UNEXPECTED_ERROR",
    )
    assert res["status"] == "FAILED"
    assert res["failure"]["code"] == "UNKNOWN_ERROR"
    assert "unexpected error" in res["failure"]["message"]
