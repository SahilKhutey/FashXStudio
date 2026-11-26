"""First-class evidence validation and abstention gate (Phase 08.3 - Tasks 8.3.4 & 8.3.5)."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.fit.contracts import EvidenceReference, FitEvidenceItem
from fashx.fit.enums import (
    FitReasonCode,
    MeasurementBasis,
    MissingDataCode,
    RecommendationStatus,
)


class FitEvidenceSecurityError(ValueError):
    """Raised when an illegal evidence type (such as VTO/generated imagery) is supplied."""


_PROHIBITED_EVIDENCE_TAGS = ("VTO", "TRYON", "TRY_ON", "GENERATED", "IMAGE", "SYNTHETIC_FIT")


def reject_prohibited_evidence(external_evidence: list[EvidenceReference] | None) -> None:
    """Enforce Phase 07.8 / 08.3 invariant: VTO images are never physical-fit evidence."""
    if not external_evidence:
        return
    for ev in external_evidence:
        upper_type = ev.source_type.strip().upper()
        if any(tag in upper_type for tag in _PROHIBITED_EVIDENCE_TAGS):
            raise FitEvidenceSecurityError(
                f"Prohibited fit evidence source type '{ev.source_type}'. "
                "Virtual try-on images cannot be used as physical fit evidence."
            )


@dataclass(frozen=True)
class EvidenceStatus:
    """Structured result of evaluating all prerequisite fit evidence gates."""

    eligible: bool
    blocking_status: RecommendationStatus | None
    reason_codes: tuple[FitReasonCode, ...]
    missing_information: tuple[MissingDataCode | str, ...]
    evidence_items: tuple[FitEvidenceItem, ...] = ()
    preference_evaluated: bool = False


def validate_evidence(
    *,
    category_enabled: bool,
    chart_exists: bool,
    chart_active: bool,
    chart_basis: MeasurementBasis | str | None,
    supported_bases: tuple[MeasurementBasis | str, ...],
    permissions_valid: bool,
    required_measurements: tuple[str, ...],
    shopper_fields: set[str],
    chart_fields: set[str],
    chart_stale: bool = False,
    has_chart_conflict: bool = False,
    merchant_isolated: bool = True,
    consent_verified: bool = True,
    stale_shopper_fields: set[str] | None = None,
    has_shopper_conflict: bool = False,
    any_variant_available: bool = True,
    has_validated_ease_policy: bool = False,
) -> EvidenceStatus:
    """Validate category, permissions, chart quality, ownership, freshness, and completeness.

    Returns an explicit, auditable EvidenceStatus and never silently skips missing data.
    """
    reasons: list[FitReasonCode] = []
    missing: list[MissingDataCode | str] = []
    items: list[FitEvidenceItem] = []
    stale_req_fields = {f.strip().upper() for f in (stale_shopper_fields or set())}
    norm_shopper = {f.strip().upper() for f in shopper_fields}
    norm_chart = {f.strip().upper() for f in chart_fields}
    norm_required = tuple(f.strip().upper() for f in required_measurements)

    norm_basis: MeasurementBasis | None = None
    if chart_basis is not None:
        try:
            norm_basis = (
                chart_basis
                if isinstance(chart_basis, MeasurementBasis)
                else MeasurementBasis(str(chart_basis).strip().upper())
            )
        except ValueError:
            norm_basis = MeasurementBasis.UNKNOWN

    norm_supported_bases: set[MeasurementBasis] = set()
    for b in supported_bases:
        try:
            norm_supported_bases.add(
                b if isinstance(b, MeasurementBasis) else MeasurementBasis(str(b).strip().upper())
            )
        except ValueError:
            continue

    blocking: RecommendationStatus | None = None

    # 1. Permissions & consent
    if not permissions_valid or not consent_verified:
        reasons.append(FitReasonCode.PERMISSION_INVALID)
        missing.append(MissingDataCode.PERMISSION_INVALID)
        items.append(FitEvidenceItem(label="Source & shopper consent", status="Invalid or missing"))
        blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
    else:
        items.append(FitEvidenceItem(label="Source & shopper consent", status="Authorized"))

    # 2. Category gate
    if not category_enabled:
        reasons.append(FitReasonCode.CATEGORY_NOT_VALIDATED)
        missing.append(MissingDataCode.CATEGORY_UNSUPPORTED)
        items.append(FitEvidenceItem(label="Category", status="Unsupported"))
        if blocking is None:
            blocking = RecommendationStatus.UNSUPPORTED_CATEGORY
    else:
        items.append(FitEvidenceItem(label="Category", status="Supported"))

    # 3. Chart existence & merchant ownership isolation
    if not chart_exists:
        reasons.append(FitReasonCode.NO_MERCHANT_CHART)
        missing.append(MissingDataCode.SIZE_CHART_MISSING)
        items.append(FitEvidenceItem(label="Merchant size chart", status="Missing"))
        if blocking in (None, RecommendationStatus.UNSUPPORTED_CATEGORY):
            if category_enabled:
                blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
    elif not merchant_isolated or has_chart_conflict:
        reasons.append(FitReasonCode.CHART_CONFLICT)
        missing.append(MissingDataCode.CHART_CONFLICT)
        items.append(FitEvidenceItem(label="Merchant size chart", status="Conflicting"))
        if blocking is None:
            blocking = RecommendationStatus.CONFLICTING_DATA
    elif chart_stale or not chart_active:
        reasons.append(FitReasonCode.STALE_CHART)
        missing.append(MissingDataCode.CHART_STALE)
        items.append(FitEvidenceItem(label="Merchant size chart", status="Stale"))
        if blocking is None:
            blocking = RecommendationStatus.STALE_DATA
    else:
        items.append(FitEvidenceItem(label="Merchant size chart", status="Current"))

    # 4. Measurement basis & ease policy separation
    if chart_exists:
        if norm_basis is None or norm_basis == MeasurementBasis.UNKNOWN:
            reasons.append(FitReasonCode.CHART_BASIS_UNSUPPORTED)
            missing.append(MissingDataCode.MEASUREMENT_BASIS_UNKNOWN)
            items.append(FitEvidenceItem(label="Measurement basis", status="Unknown"))
            if blocking is None:
                blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
        elif norm_basis == MeasurementBasis.GARMENT and not has_validated_ease_policy:
            reasons.append(FitReasonCode.EASE_POLICY_MISSING)
            missing.append(MissingDataCode.FIT_POLICY_MISSING)
            items.append(
                FitEvidenceItem(label="Garment ease policy", status="Missing validated ease rules")
            )
            if blocking is None:
                blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
        elif norm_basis not in norm_supported_bases:
            reasons.append(FitReasonCode.CHART_BASIS_UNSUPPORTED)
            missing.append(MissingDataCode.FIT_POLICY_MISSING)
            items.append(FitEvidenceItem(label="Measurement basis", status="Unsupported for policy"))
            if blocking is None:
                blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
        else:
            items.append(FitEvidenceItem(label="Measurement basis", status=norm_basis.value))

    # 5. Shopper proportion / measurement conflict check
    if has_shopper_conflict:
        reasons.append(FitReasonCode.CHART_CONFLICT)
        items.append(FitEvidenceItem(label="Shopper measurements", status="Conflicting proportions"))
        if blocking is None:
            blocking = RecommendationStatus.CONFLICTING_DATA

    # 6. Required shopper measurements (missing vs stale)
    missing_shopper = [f for f in norm_required if f not in norm_shopper]
    stale_req = [f for f in norm_required if f in stale_req_fields and f in norm_shopper]

    if missing_shopper:
        reasons.append(FitReasonCode.MISSING_REQUIRED_MEASUREMENT)
        missing.append(MissingDataCode.SHOPPER_MEASUREMENT_MISSING)
        for field in missing_shopper:
            missing.append(field)
        items.append(
            FitEvidenceItem(
                label=f"Shopper {', '.join(missing_shopper).lower()} measurement",
                status="Missing",
            )
        )
        if blocking is None:
            blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
    elif stale_req:
        reasons.append(FitReasonCode.STALE_SHOPPER_MEASUREMENT)
        missing.append(MissingDataCode.SHOPPER_MEASUREMENT_STALE)
        items.append(
            FitEvidenceItem(
                label=f"Shopper {', '.join(stale_req).lower()} measurement",
                status="Stale (needs confirmation)",
            )
        )
        if blocking is None:
            blocking = RecommendationStatus.STALE_DATA
    elif norm_required:
        items.append(
            FitEvidenceItem(
                label=f"Shopper {', '.join(norm_required).lower()} measurement",
                status="Available",
            )
        )

    # 7. Required chart measurements
    if chart_exists:
        missing_chart = [f for f in norm_required if f not in norm_chart]
        if missing_chart:
            if FitReasonCode.NO_MERCHANT_CHART not in reasons:
                reasons.append(FitReasonCode.NO_MERCHANT_CHART)
            if MissingDataCode.SIZE_CHART_MISSING not in missing:
                missing.append(MissingDataCode.SIZE_CHART_MISSING)
            items.append(
                FitEvidenceItem(
                    label=f"Merchant {', '.join(missing_chart).lower()} chart",
                    status="Missing fields",
                )
            )
            if blocking is None:
                blocking = RecommendationStatus.INSUFFICIENT_INFORMATION
        elif norm_required:
            items.append(
                FitEvidenceItem(
                    label=f"Merchant {', '.join(norm_required).lower()} chart",
                    status="Available",
                )
            )

    # 8. Variant availability check (only block if we otherwise would evaluate variants)
    if not any_variant_available:
        reasons.append(FitReasonCode.VARIANT_UNAVAILABLE)
        missing.append(MissingDataCode.VARIANT_UNAVAILABLE)
        items.append(FitEvidenceItem(label="Available variants", status="None available"))
        if blocking is None:
            blocking = RecommendationStatus.NO_AVAILABLE_SIZE

    eligible = blocking is None and len(reasons) == 0
    return EvidenceStatus(
        eligible=eligible,
        blocking_status=blocking,
        reason_codes=tuple(dict.fromkeys(reasons)),
        missing_information=tuple(dict.fromkeys(missing)),
        evidence_items=tuple(items),
        preference_evaluated=has_validated_ease_policy,
    )
