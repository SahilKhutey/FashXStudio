"""FASHN API Error Mapping and Normalization Module.

Translates vendor-specific HTTP error codes and asynchronous payload error names
into domain-neutral TryOnError exceptions with clear retryability and user messages.
"""

from __future__ import annotations

import logging
from typing import Any

from fashx.application.ports.tryon import TryOnError
from fashx.core.metrics import emit_metric

log = logging.getLogger(__name__)

# Error categories from FASHN status payload
NON_RETRYABLE_USER_ERRORS = {
    "imageloaderror",
    "poseerror",
    "nopersondetectederror",
    "facedetectionerror",
    "garmentdetectionerror",
    "invalidimageerror",
    "imagesizetoosmall",
    "imagesizetoolarge",
    "unsupportedimageformat",
}

POLICY_VIOLATION_ERRORS = {
    "contentpolicyviolation",
    "nsfwdetected",
    "safetycheckfailed",
    "moderationerror",
}

RETRYABLE_PROVIDER_ERRORS = {
    "pipelineerror",
    "modeltimeout",
    "gpuoutofmemory",
    "internalerror",
    "serviceunavailable",
    "temporaryerror",
    "concurrencyexceeded",
}


def map_fashn_http_error(
    status_code: int,
    response_body: str,
    *,
    environment: str = "dev",
    provider: str = "fashn_api",
    model: str = "tryon-v1.6",
) -> TryOnError:
    """Map HTTP response errors from FASHN API to normalized TryOnError."""
    body_snippet = (response_body or "")[:200].strip()

    if status_code == 429:
        emit_metric(
            "VTOProviderRateLimit",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model},
            namespace="FashX/VTO",
        )
        emit_metric(
            "VTOJobFailed",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model, "Outcome": "http_429"},
            namespace="FashX/VTO",
        )
        return TryOnError(
            "provider_unavailable",
            "Try-on is busy. We'll retry shortly.",
            retryable=True,
            detail=f"http 429: rate limited: {body_snippet}",
        )

    if status_code in (401, 403):
        emit_metric(
            "VTOProviderAuthFailure",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model},
            namespace="FashX/VTO",
        )
        emit_metric(
            "VTOJobFailed",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model, "Outcome": f"http_{status_code}"},
            namespace="FashX/VTO",
        )
        return TryOnError(
            "provider_auth",
            "Try-on is temporarily unavailable.",
            retryable=False,
            detail=f"auth rejected (check key): http {status_code}",
        )

    if status_code == 402:
        emit_metric(
            "VTOJobFailed",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model, "Outcome": "http_402"},
            namespace="FashX/VTO",
        )
        return TryOnError(
            "provider_credits",
            "Try-on is temporarily unavailable.",
            retryable=False,
            detail=f"credits exhausted: http 402: {body_snippet}",
        )

    if status_code in (500, 502, 503, 504):
        emit_metric(
            "VTOJobFailed",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model, "Outcome": f"http_{status_code}"},
            namespace="FashX/VTO",
        )
        return TryOnError(
            "provider_unavailable",
            "Try-on is busy. We'll retry shortly.",
            retryable=True,
            detail=f"http {status_code}: {body_snippet}",
        )

    if status_code == 400:
        emit_metric(
            "VTOJobFailed",
            1.0,
            unit="Count",
            service="tryon",
            environment=environment,
            dimensions={"Provider": provider, "ModelVersion": model, "Outcome": "http_400"},
            namespace="FashX/VTO",
        )
        return TryOnError(
            "bad_input",
            "We couldn't use this photo or garment. Try another photo.",
            retryable=False,
            detail=f"http 400: {body_snippet}",
        )

    # General unexpected status
    emit_metric(
        "VTOJobFailed",
        1.0,
        unit="Count",
        service="tryon",
        environment=environment,
        dimensions={"Provider": provider, "ModelVersion": model, "Outcome": f"http_{status_code}"},
        namespace="FashX/VTO",
    )
    return TryOnError(
        "bad_input",
        "We couldn't use this photo or garment. Try another photo.",
        retryable=False,
        detail=f"http {status_code}: {body_snippet}",
    )


def map_fashn_status_error(
    error_name: str | None,
    error_message: str | None = None,
    *,
    environment: str = "dev",
    provider: str = "fashn_api",
    model: str = "tryon-v1.6",
    raw_error: Any = None,
) -> TryOnError:
    """Map asynchronous status error payloads from FASHN polling to normalized TryOnError."""
    name_clean = (error_name or "unknown").strip().lower()
    detail_str = str(error_message or error_name or "provider execution failed")[:200]

    emit_metric(
        "VTOJobFailed",
        1.0,
        unit="Count",
        service="tryon",
        environment=environment,
        dimensions={"Provider": provider, "ModelVersion": model, "Outcome": f"fashn_{name_clean}"},
        namespace="FashX/VTO",
    )

    if name_clean in POLICY_VIOLATION_ERRORS:
        return TryOnError(
            "policy_violation",
            "This photo or garment could not be processed due to safety guidelines.",
            retryable=False,
            detail=detail_str,
        )

    if name_clean in NON_RETRYABLE_USER_ERRORS:
        if "person" in name_clean or "pose" in name_clean or "face" in name_clean:
            msg = "We couldn't detect a person in your photo. Try another photo."
        elif "garment" in name_clean:
            msg = "We couldn't detect the garment. Try another garment photo."
        else:
            msg = "We couldn't use this photo or garment. Try another photo."
        return TryOnError(
            "bad_input",
            msg,
            retryable=False,
            detail=detail_str,
        )

    if name_clean in RETRYABLE_PROVIDER_ERRORS:
        return TryOnError(
            "provider_unavailable",
            "Try-on took too long or encountered a temporary issue. We'll retry.",
            retryable=True,
            detail=detail_str,
        )

    # Default fallback for unrecognized provider errors
    log.warning("Unmapped FASHN error encountered: %s: %s", error_name, error_message)
    return TryOnError(
        "provider_failed",
        "We couldn't generate this try-on. Try another photo or garment.",
        retryable=False,
        detail=detail_str,
    )
