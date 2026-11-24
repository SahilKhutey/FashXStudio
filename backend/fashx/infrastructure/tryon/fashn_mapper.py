"""FASHN API Request/Response Schema Mapper.

Provides isolation between internal FashX domain representations and FASHN vendor
API contracts (Try-On v1.6 and Try-On Max).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

from fashx.application.ports.tryon import TryOnRequest

# Standard FASHN statuses
FASHN_PENDING_STATUSES = {"starting", "in_queue", "processing"}
FASHN_SUCCESS_STATUSES = {"completed"}
FASHN_FAILURE_STATUSES = {"failed", "canceled", "cancelled"}
FASHN_TIMEOUT_STATUSES = {"time_out"}


def bytes_to_b64_data_uri(jpeg_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encode binary image to a data URI for FASHN API payloads."""
    encoded = base64.b64encode(jpeg_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@dataclass(frozen=True)
class FashnStatusResult:
    """Normalized representation of FASHN status polling response."""

    status: str
    is_terminal: bool
    is_success: bool
    output_urls: list[str] = field(default_factory=list)
    error_name: str | None = None
    error_message: str | None = None
    credits_used: float | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


def build_fashn_run_payload(
    req: TryOnRequest,
    model: str = "tryon-v1.6",
    mode: str | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map domain TryOnRequest to FASHN /run JSON payload.

    Supports both tryon-v1.6 and tryon-max models.
    """
    category = req.category if req.category in ("tops", "bottoms", "one-pieces") else "auto"

    inputs: dict[str, Any] = {
        "model_image": bytes_to_b64_data_uri(req.person_jpeg),
        "garment_image": bytes_to_b64_data_uri(req.garment_jpeg),
        "category": category,
    }

    if mode:
        inputs["mode"] = mode

    # Merge model-specific options if provided
    if options:
        for key, val in options.items():
            if val is not None and key not in inputs:
                inputs[key] = val

    return {
        "model_name": model,
        "inputs": inputs,
    }


def parse_fashn_status_response(
    data: dict[str, Any],
    headers: dict[str, str] | None = None,
    default_cost_credits: float = 1.0,
) -> FashnStatusResult:
    """Parse raw FASHN status polling response into normalized FashnStatusResult.

    Extracts output image URLs, failure information, and credit consumption.
    """
    raw_status = str(data.get("status", "")).strip().lower()
    is_success = raw_status in FASHN_SUCCESS_STATUSES
    is_terminal = (
        is_success
        or raw_status in FASHN_FAILURE_STATUSES
        or raw_status in FASHN_TIMEOUT_STATUSES
    )

    output_urls: list[str] = []
    output_val = data.get("output")
    if isinstance(output_val, list):
        output_urls = [str(u) for u in output_val if u]
    elif isinstance(output_val, str) and output_val.strip():
        output_urls = [output_val.strip()]

    error_name: str | None = None
    error_message: str | None = None
    err_obj = data.get("error")
    if isinstance(err_obj, dict):
        error_name = str(err_obj.get("name") or err_obj.get("code") or "unknown_error")
        error_message = str(err_obj.get("message") or err_obj.get("detail") or error_name)
    elif isinstance(err_obj, str) and err_obj.strip():
        error_name = err_obj.strip()
        error_message = err_obj.strip()

    # Extract credits used from response headers or body
    credits_used: float | None = None
    if headers:
        header_credits = headers.get("x-fashn-credits-used") or headers.get("X-Fashn-Credits-Used")
        if header_credits:
            try:
                credits_used = float(header_credits)
            except (ValueError, TypeError):
                credits_used = None

    if credits_used is None and "credits_used" in data:
        try:
            credits_used = float(data["credits_used"])
        except (ValueError, TypeError):
            credits_used = None

    if credits_used is None and "credits" in data:
        try:
            credits_used = float(data["credits"])
        except (ValueError, TypeError):
            credits_used = None

    if credits_used is None and is_success:
        credits_used = default_cost_credits

    return FashnStatusResult(
        status=raw_status,
        is_terminal=is_terminal,
        is_success=is_success,
        output_urls=output_urls,
        error_name=error_name,
        error_message=error_message,
        credits_used=credits_used,
        raw_response=data,
    )
