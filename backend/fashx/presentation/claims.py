from __future__ import annotations

import re
from enum import Enum
from typing import Any


class ClaimType(str, Enum):
    VISUAL_SIMULATION = "VISUAL_SIMULATION"
    SIZE_CHART = "SIZE_CHART"
    FIT_RECOMMENDATION = "FIT_RECOMMENDATION"
    FIT_GUARANTEE = "FIT_GUARANTEE"
    VERIFIED_FIT = "VERIFIED_FIT"


CLAIM_COPY: dict[ClaimType, dict[str, str]] = {
    ClaimType.VISUAL_SIMULATION: {
        "title": "AI-generated visual try-on",
        "heading": "Virtual Try-On",
        "caption": "AI-generated visual simulation",
        "status": "Visual result generated",
        "description": (
            "See how this garment might look on you. "
            "This visual simulation does not verify physical size or fit."
        ),
        "disclaimer": "Visual try-on does not verify physical fit",
        "secondary": "Check the merchant's size chart and available fit guidance before selecting a size.",
        "action": "View merchant size chart",
    },
    ClaimType.SIZE_CHART: {
        "title": "Merchant size chart",
        "heading": "Size and fit information",
        "description": "Review the size information supplied by the merchant.",
        "source_label": "Merchant supplied",
        "empty_message": "The merchant has not provided a verified size chart for this product.",
        "stale_warning": "This size information has not been verified against the latest merchant source.",
    },
    ClaimType.FIT_RECOMMENDATION: {
        "title": "Fit guidance",
        "description": (
            "This recommendation is based on the available measurements and product data. "
            "It is not a guarantee of fit."
        ),
        "unavailable_title": "Fit recommendation unavailable",
        "unavailable_description": (
            "We do not have enough verified information to recommend a size for this product. "
            "You can review the merchant's size chart before selecting a size."
        ),
    },
}

# Strict blacklist of phrases that must NEVER be used in visual try-on contexts
PROHIBITED_CLAIM_PATTERNS: tuple[str, ...] = (
    "guaranteed fit",
    "guarantee fit",
    "guaranteed-fit",
    "perfect fit",
    "perfect-fit",
    "verified fit",
    "verified physical fit",
    "your exact body fit",
    "exact body fit",
    "this size will fit you",
    "true-to-size confirmation",
    "physically accurate fit",
    "size confirmed by ai",
    "never get the wrong size again",
    "find your perfect fit",
    "know your exact size",
    "ai confirms this garment fits",
    "guaranteed before purchase",
)


def validate_claim_text(text: str) -> bool:
    """Validate that copy does not make unsupported fit or sizing guarantee claims."""
    if not text:
        return True
    normalized = re.sub(r"[^\w\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    for pattern in PROHIBITED_CLAIM_PATTERNS:
        pattern_norm = re.sub(r"[^\w\s]", " ", pattern.lower())
        pattern_norm = re.sub(r"\s+", " ", pattern_norm).strip()
        if pattern_norm in normalized:
            return False
    return True


def assert_claim_valid(text: str) -> None:
    """Assert copy compliance with Phase 07.8 content policy."""
    if not validate_claim_text(text):
        raise ValueError(
            "Copy violates Phase 07.8 policy: unsupported guaranteed fit or verified fit claim detected."
        )


def get_presentation_policy(
    result_type: str = "VISUAL_TRY_ON",
    fit_recommendation_available: bool = False,
) -> dict[str, Any]:
    """Server-authoritative presentation policy for Virtual Try-On results.

    Enforces that client-side overrides cannot convert a VISUAL_TRY_ON simulation
    into a VERIFIED_FIT or claim fit guarantees.
    """
    # Enforce server authority: cannot be overridden to VERIFIED_FIT or GUARANTEE
    sanitized_result_type = "VISUAL_TRY_ON"
    return {
        "presentation": {
            "result_type": sanitized_result_type,
            "is_ai_generated": True,
            "fit_verified": False,
            "fit_prediction_id": None,
            "disclaimer_code": "VISUAL_TRYON_NOT_FIT_VERIFICATION",
            "fit_recommendation_available": fit_recommendation_available,
            "fit_guaranteed": False,
            "policy_version": "presentation-v1",
            "copy": CLAIM_COPY[ClaimType.VISUAL_SIMULATION],
        }
    }


def enforce_merchant_widget_policy(custom_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sanitize and enforce merchant storefront widget presentation rules.

    Merchants may customize: theme, logo, button styling, layout, product placement.
    Merchants CANNOT:
      - Remove or hide the visual simulation disclaimer
      - Change result_type to VERIFIED_FIT
      - Make fit guarantee claims
      - Suppress size chart provenance
    """
    base_config = {
        "theme": {},
        "show_disclaimer": True,
        "disclaimer_text": CLAIM_COPY[ClaimType.VISUAL_SIMULATION]["disclaimer"],
        "result_label": CLAIM_COPY[ClaimType.VISUAL_SIMULATION]["title"],
        "disclaimer_locked": True,
        "allow_fit_guarantee": False,
    }
    if not custom_config:
        return base_config

    result = dict(custom_config)
    # Re-enforce mandatory non-negotiables
    result["show_disclaimer"] = True
    result["disclaimer_locked"] = True
    result["allow_fit_guarantee"] = False

    # Check custom label or text
    custom_label = str(result.get("result_label", ""))
    if not validate_claim_text(custom_label):
        result["result_label"] = CLAIM_COPY[ClaimType.VISUAL_SIMULATION]["title"]

    custom_disc = str(result.get("disclaimer_text", ""))
    if not validate_claim_text(custom_disc) or not custom_disc.strip():
        result["disclaimer_text"] = CLAIM_COPY[ClaimType.VISUAL_SIMULATION]["disclaimer"]

    return result
