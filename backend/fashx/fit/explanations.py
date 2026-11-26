"""Approved shopper-facing reason-code explanations and anti-guarantee guard (Phase 08.3 - Task 8.3.9)."""

from __future__ import annotations

import re

from fashx.fit.enums import FitReasonCode, MissingDataCode

EXPLANATIONS: dict[str, str] = {
    FitReasonCode.WITHIN_PUBLISHED_RANGE.value: (
        "Your measurement falls within the merchant's published range for this size."
    ),
    FitReasonCode.ALL_REQUIRED_MEASUREMENTS_MATCH.value: (
        "All required measurements match the available merchant size chart."
    ),
    FitReasonCode.MULTIPLE_SIZES_MATCH.value: (
        "More than one size matches the published measurements. We cannot select a single size confidently."
    ),
    FitReasonCode.MISSING_REQUIRED_MEASUREMENT.value: (
        "Some information is missing. Add the requested measurement to receive size guidance."
    ),
    FitReasonCode.NO_MERCHANT_CHART.value: (
        "This product does not have a usable merchant size chart."
    ),
    FitReasonCode.CHART_BASIS_UNSUPPORTED.value: (
        "The measurement basis is not clear enough to make a recommendation."
    ),
    FitReasonCode.PREFERENCE_NOT_EVALUATED.value: (
        "Your fit preference could not be evaluated from the available garment data."
    ),
    FitReasonCode.CATEGORY_NOT_VALIDATED.value: (
        "Size guidance is not yet available for this garment category."
    ),
    FitReasonCode.NO_MATCHING_SIZE.value: (
        "None of the currently available sizes matches all required published measurements."
    ),
    FitReasonCode.STALE_CHART.value: (
        "The merchant's size chart is outside the freshness window. Inspect the chart directly."
    ),
    FitReasonCode.STALE_SHOPPER_MEASUREMENT.value: (
        "Your saved measurements need confirmation or updating before calculating new guidance."
    ),
    FitReasonCode.CHART_CONFLICT.value: (
        "Available measurement or merchant size chart records conflict and cannot be used safely."
    ),
    FitReasonCode.PERMISSION_INVALID.value: (
        "Required consent or merchant source authorization is missing or withdrawn."
    ),
    FitReasonCode.VARIANT_UNAVAILABLE.value: (
        "No active, available product variants were found for sizing."
    ),
    FitReasonCode.EASE_POLICY_MISSING.value: (
        "This garment uses finished-garment dimensions without a validated ease policy for this category."
    ),
    FitReasonCode.EASE_WITHIN_POLICY.value: (
        "Calculated garment ease falls within the validated policy range for this intended fit."
    ),
    FitReasonCode.OUTSIDE_EASE_POLICY.value: (
        "Calculated garment ease falls outside the validated policy range for this intended fit."
    ),
}

_PROHIBITED_GUARANTEE_PATTERNS = (
    re.compile(r"\bguaranteed?\s+(to\s+)?fit\b", re.IGNORECASE),
    re.compile(r"\b100%\s*(accurate|fit|guarantee)\b", re.IGNORECASE),
    re.compile(r"\bverified\s+physical\s+fit\b", re.IGNORECASE),
    re.compile(r"\bproven\s+(to\s+)?fit\b", re.IGNORECASE),
    re.compile(r"\bexact\s+fit\s+guaranteed\b", re.IGNORECASE),
    re.compile(r"\bwill\s+definitely\s+fit\b", re.IGNORECASE),
)


def assert_no_guarantee_language(text: str) -> None:
    """Raise ValueError if user-facing copy violates no-fit-guarantee policy."""
    for pat in _PROHIBITED_GUARANTEE_PATTERNS:
        if pat.search(text):
            raise ValueError(f"Prohibited fit-guarantee language detected in copy: '{text}'")


def explain(reason_codes: list[FitReasonCode | str]) -> list[str]:
    """Map machine-readable reason codes strictly to approved, non-guarantee explanations."""
    messages: list[str] = []
    for raw in reason_codes:
        key = raw.value if isinstance(raw, FitReasonCode) else str(raw)
        msg = EXPLANATIONS.get(key)
        if msg:
            assert_no_guarantee_language(msg)
            messages.append(msg)
    return messages


def build_summary_explanation(
    *,
    reason_codes: list[FitReasonCode | str],
    recommended_label: str | None = None,
    alternative_labels: list[str] | None = None,
) -> tuple[list[str], str]:
    """Produce ordered explanation list and a concise lead summary."""
    lines = explain(reason_codes)
    if recommended_label:
        summary = (
            f"Size {recommended_label} matches your available measurements on this merchant's "
            "published size chart."
        )
    elif alternative_labels:
        summary = (
            f"Sizes {', '.join(alternative_labels)} all match your available measurements; "
            "review the merchant chart to compare fit."
        )
    elif lines:
        summary = lines[0]
    else:
        summary = "We cannot provide a size recommendation from the currently available evidence."
    assert_no_guarantee_language(summary)
    return lines, summary


def build_next_actions(missing_information: list[MissingDataCode | str]) -> list[str]:
    """Suggest actionable next steps when information is missing or stale."""
    actions: list[str] = []
    codes = {m.value if isinstance(m, MissingDataCode) else str(m) for m in missing_information}
    if MissingDataCode.SHOPPER_MEASUREMENT_MISSING.value in codes:
        actions.append("Add the missing measurement in your Fit Profile.")
    if MissingDataCode.SHOPPER_MEASUREMENT_STALE.value in codes:
        actions.append("Confirm or update your saved measurements in Fit Profile.")
    if MissingDataCode.SIZE_CHART_MISSING.value in codes or MissingDataCode.CHART_STALE.value in codes:
        actions.append("Review the merchant's product details for sizing information.")
    if MissingDataCode.PERMISSION_INVALID.value in codes:
        actions.append("Enable fit recommendation consent in privacy settings.")
    if MissingDataCode.FIT_POLICY_MISSING.value in codes:
        actions.append("Inspect the merchant's published size chart manually.")
    return actions
