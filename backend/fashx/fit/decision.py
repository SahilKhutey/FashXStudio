"""Deterministic candidate evaluation and recommendation decision policy (Phase 08.3 - Tasks 8.3.7 & 8.3.8)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fashx.fit.confidence import (
    DEFAULT_INTERNAL_THRESHOLD,
    calculate_evidence_score,
    may_recommend,
)
from fashx.fit.contracts import (
    MeasurementValue,
    MerchantSizeOption,
    RecommendedSizeDetail,
)
from fashx.fit.ease_policy import EaseRule
from fashx.fit.enums import (
    FitPreference,
    FitReasonCode,
    MeasurementBasis,
    RecommendationStatus,
)
from fashx.fit.measurement_matcher import evaluate_size_detailed


@dataclass(frozen=True)
class CandidateDecisionOutcome:
    """Auditable candidate evaluation output prior to explanation and snapshot assembly."""

    status: RecommendationStatus
    recommended_size: RecommendedSizeDetail | None
    alternative_sizes: tuple[RecommendedSizeDetail, ...]
    reason_codes: tuple[FitReasonCode, ...]
    evaluated_candidates: tuple[dict[str, object], ...]
    preference_evaluated: bool


def recommend_size(
    *,
    shopper_measurements: dict[str, MeasurementValue],
    sizes: list[MerchantSizeOption],
    required_fields: tuple[str, ...],
    evidence_eligible: bool,
    blocking_status: RecommendationStatus | None = None,
    blocking_reasons: tuple[FitReasonCode, ...] = (),
    optional_fields: tuple[str, ...] = (),
    chart_basis: MeasurementBasis = MeasurementBasis.BODY,
    ease_rules: dict[str, EaseRule] | None = None,
    fit_preference: FitPreference = FitPreference.NO_PREFERENCE,
    confidence_dimensions: dict[str, Decimal] | None = None,
    internal_threshold: Decimal = DEFAULT_INTERNAL_THRESHOLD,
) -> CandidateDecisionOutcome:
    """Select an unambiguous matching available size, expose alternatives, or abstain cleanly."""
    if not evidence_eligible:
        return CandidateDecisionOutcome(
            status=blocking_status or RecommendationStatus.INSUFFICIENT_INFORMATION,
            recommended_size=None,
            alternative_sizes=(),
            reason_codes=blocking_reasons or (FitReasonCode.MISSING_REQUIRED_MEASUREMENT,),
            evaluated_candidates=(),
            preference_evaluated=False,
        )

    if confidence_dimensions is not None:
        score = calculate_evidence_score(confidence_dimensions)
        if not may_recommend(
            evidence_eligible=evidence_eligible,
            score=score,
            internal_threshold=internal_threshold,
        ):
            return CandidateDecisionOutcome(
                status=RecommendationStatus.INSUFFICIENT_INFORMATION,
                recommended_size=None,
                alternative_sizes=(),
                reason_codes=(FitReasonCode.MISSING_REQUIRED_MEASUREMENT,),
                evaluated_candidates=(),
                preference_evaluated=False,
            )

    available_sizes = [s for s in sizes if s.available]
    if not available_sizes:
        return CandidateDecisionOutcome(
            status=RecommendationStatus.NO_AVAILABLE_SIZE,
            recommended_size=None,
            alternative_sizes=(),
            reason_codes=(FitReasonCode.VARIANT_UNAVAILABLE,),
            evaluated_candidates=(),
            preference_evaluated=False,
        )

    matching: list[RecommendedSizeDetail] = []
    candidate_records: list[dict[str, object]] = []
    any_ease_evaluated = False

    for idx, option in enumerate(sizes):
        detail = evaluate_size_detailed(
            shopper_measurements=shopper_measurements,
            size_ranges=option.measurements,
            required_fields=required_fields,
            optional_fields=optional_fields,
            chart_basis=chart_basis,
            ease_rules=ease_rules,
        )
        any_ease_evaluated = any_ease_evaluated or detail.ease_evaluated
        candidate_records.append(
            {
                "variant_id": option.variant_id,
                "merchant_size_label": option.merchant_size_label,
                "is_available": option.available,
                "matched": detail.matched,
                "mismatched_fields": list(detail.mismatched_fields),
                "rank_order": idx,
            }
        )
        if detail.matched and option.available:
            matching.append(
                RecommendedSizeDetail(
                    variant_id=option.variant_id,
                    merchant_size_label=option.merchant_size_label,
                )
            )

    extra_reasons: list[FitReasonCode] = []
    if fit_preference != FitPreference.NO_PREFERENCE and not any_ease_evaluated:
        extra_reasons.append(FitReasonCode.PREFERENCE_NOT_EVALUATED)

    if not matching:
        return CandidateDecisionOutcome(
            status=RecommendationStatus.NO_AVAILABLE_SIZE,
            recommended_size=None,
            alternative_sizes=(),
            reason_codes=(FitReasonCode.NO_MATCHING_SIZE, *extra_reasons),
            evaluated_candidates=tuple(candidate_records),
            preference_evaluated=any_ease_evaluated,
        )

    if len(matching) > 1:
        # Section 9.2: When multiple sizes match and no validated tie-breaker/ease rule
        # distinguishes one winner, return POSSIBLE_ALTERNATIVES rather than guessing.
        return CandidateDecisionOutcome(
            status=RecommendationStatus.POSSIBLE_ALTERNATIVES,
            recommended_size=None,
            alternative_sizes=tuple(matching),
            reason_codes=(FitReasonCode.MULTIPLE_SIZES_MATCH, *extra_reasons),
            evaluated_candidates=tuple(candidate_records),
            preference_evaluated=any_ease_evaluated,
        )

    winner = matching[0]
    reasons = [
        FitReasonCode.WITHIN_PUBLISHED_RANGE,
        FitReasonCode.ALL_REQUIRED_MEASUREMENTS_MATCH,
    ]
    if any_ease_evaluated:
        reasons.append(FitReasonCode.EASE_WITHIN_POLICY)
    reasons.extend(extra_reasons)

    return CandidateDecisionOutcome(
        status=RecommendationStatus.RECOMMENDED,
        recommended_size=winner,
        alternative_sizes=(),
        reason_codes=tuple(reasons),
        evaluated_candidates=tuple(candidate_records),
        preference_evaluated=any_ease_evaluated,
    )
