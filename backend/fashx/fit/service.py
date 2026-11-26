"""Fit Recommendation Service (Phase 07.8 compatibility + Phase 08.3 evidence engine)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fashx.catalog.size_charts.enums import AvailabilityStatus, SizeChartStatus
from fashx.catalog.size_charts.schemas import (
    MeasurementBasis as CatalogMeasurementBasis,
)
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    ProductSizeChartResponse,
    ProductVariantAvailability,
)
from fashx.fit.category_policy import (
    CategoryFitPolicy,
    get_category_fit_policy,
    normalize_category_code,
)
from fashx.fit.confidence import (
    DEFAULT_INTERNAL_THRESHOLD,
    build_evidence_dimensions,
    calculate_evidence_score,
)
from fashx.fit.contracts import (
    FIT_ALGORITHM_VERSION,
    ConfidenceSummary,
    EvidenceReference,
    FitEvidenceSummary,
    FitModelSpec,
    FitOutcome,
    FitProductInput,
    FitRecommendationResponse,
    FitRecommendationResult,
    MeasurementValue,
    MerchantSizeOption,
    RecommendedSizeDetail,
    ShopperMeasurementsInput,
    SizeRange,
)
from fashx.fit.decision import recommend_size
from fashx.fit.ease_policy import DEFAULT_EASE_REGISTRY, EasePolicyRegistry, EaseRule
from fashx.fit.enums import (
    ConfidenceType,
    FitPreference,
    FitReasonCode,
    MeasurementBasis,
    MissingDataCode,
    RecommendationStatus,
)
from fashx.fit.evidence import (
    FitEvidenceSecurityError,
    reject_prohibited_evidence,
    validate_evidence,
)
from fashx.fit.explanations import build_next_actions, build_summary_explanation
from fashx.fit.repository import FitRecommendationRepository
from fashx.profile.validation import evaluate_measurement_freshness

__all__ = ["FitEvidenceSecurityError", "FitRecommendationService"]


def _size_ranges_from_chart(
    chart: ProductSizeChartResponse,
    availability: ProductVariantAvailability | None,
) -> tuple[list[MerchantSizeOption], bool]:
    """Convert Phase 08.1 chart rows and availability into MerchantSizeOptions.

    Returns (options, has_chart_conflict).
    """
    basis = MeasurementBasis(chart.measurement_basis.value)
    avail_by_label: dict[str, tuple[str, bool, str]] = {}
    if availability is not None:
        for var in availability.variants:
            norm_label = var.size_label.strip().upper()
            is_avail = var.status in (
                AvailabilityStatus.IN_STOCK,
                AvailabilityStatus.LOW_STOCK,
                AvailabilityStatus.PREORDER,
            )
            # Prefer an available variant if multiple colors share a size label
            if norm_label not in avail_by_label or is_avail:
                avail_by_label[norm_label] = (var.variant_id, is_avail, var.status.value)

    options: list[MerchantSizeOption] = []
    seen_labels: set[str] = set()
    has_conflict = False

    for row in chart.rows:
        label = row.merchant_size.strip()
        norm_label = label.upper()
        if norm_label in seen_labels:
            has_conflict = True
        seen_labels.add(norm_label)

        ranges: list[SizeRange] = []
        seen_fields: set[str] = set()
        for m in row.measurements:
            field_code = m.field_code.strip().upper()
            if field_code in seen_fields:
                has_conflict = True
            seen_fields.add(field_code)
            val = Decimal(str(m.normalized_cm))
            # Support optional range bounds if present on extended measurement objects
            min_raw = getattr(m, "minimum_cm", None) or getattr(m, "min_cm", None)
            max_raw = getattr(m, "maximum_cm", None) or getattr(m, "max_cm", None)
            low = Decimal(str(min_raw)) if min_raw is not None else val
            high = Decimal(str(max_raw)) if max_raw is not None else val
            if low > high:
                has_conflict = True
                low, high = high, low
            ranges.append(
                SizeRange(
                    field=field_code,
                    minimum_cm=low,
                    maximum_cm=high,
                    original_unit=m.unit.value,
                    basis=basis,
                )
            )

        if availability is not None and availability.variants:
            var_info = avail_by_label.get(norm_label)
            if var_info is None:
                var_id = f"{chart.merchant_product_id}:{label}"
                is_avail = False
                avail_stat = AvailabilityStatus.OUT_OF_STOCK.value
            else:
                var_id, is_avail, avail_stat = var_info
        else:
            var_id = f"{chart.merchant_product_id}:{label}"
            is_avail = True
            avail_stat = AvailabilityStatus.IN_STOCK.value

        options.append(
            MerchantSizeOption(
                variant_id=var_id,
                merchant_size_label=label,
                available=is_avail,
                availability_status=avail_stat,
                measurements=ranges,
            )
        )

    return options, has_conflict


class FitRecommendationService:
    """Evidence-based fit recommendation service supporting Phase 07.8 & Phase 08.3.

    Strict Invariants:
    1. Visual Try-On outputs CANNOT be consumed as proof or evidence of physical fit.
    2. Body measurements and garment measurements are strictly distinct bases.
    3. Every recommendation is scoped to an exact merchant product, offer, and chart revision.
    4. Missing, stale, conflicting, or unauthorized data causes explicit abstention.
    5. Confidence scores remain internal unless calibration is demonstrated.
    6. Fit guarantees are strictly prohibited (`fit_guaranteed = False`).
    """

    def __init__(
        self,
        session_or_db: Any = None,
        *,
        repository: FitRecommendationRepository | None = None,
        ease_registry: EasePolicyRegistry | None = None,
    ) -> None:
        self.session = session_or_db
        self.repo = repository or FitRecommendationRepository(session_or_db)
        self.ease_registry = ease_registry or DEFAULT_EASE_REGISTRY

    # -----------------------------------------------------------------------
    # Phase 08.3 Evidence-Based Engine
    # -----------------------------------------------------------------------

    async def evaluate_recommendation(
        self,
        *,
        shopper_id: UUID | str,
        product_id: UUID | str,
        merchant_offer_id: UUID | str | None,
        merchant_id: UUID | str | None,
        merchant_product_id: UUID | str | None,
        category: str,
        shopper_measurements: dict[str, MeasurementValue],
        shopper_measurement_revision: int | None = None,
        consent_verified: bool = True,
        permissions_valid: bool = True,
        source_permission_revision: int | None = None,
        fit_preference: FitPreference = FitPreference.NO_PREFERENCE,
        fit_preference_revision: int | None = None,
        chart: ProductSizeChartResponse | None = None,
        availability: ProductVariantAvailability | None = None,
        size_options_override: list[MerchantSizeOption] | None = None,
        chart_basis_override: MeasurementBasis | None = None,
        policy_overrides: dict[str, CategoryFitPolicy] | None = None,
        external_evidence: list[EvidenceReference] | None = None,
        internal_threshold: Decimal = DEFAULT_INTERNAL_THRESHOLD,
        persist_snapshot: bool = True,
    ) -> FitRecommendationResult:
        """Execute auditable Phase 08.3 evidence gates, matcher, confidence, and snapshot persistence."""
        reject_prohibited_evidence(external_evidence)

        rec_uuid = uuid.uuid4()
        rec_id = str(rec_uuid)
        norm_cat = normalize_category_code(category)
        policy = get_category_fit_policy(norm_cat, overrides=policy_overrides)
        category_enabled = policy is not None and policy.enabled

        # Check merchant-isolation on chart vs resolved offer/merchant_product
        chart_exists = chart is not None and bool(chart.rows)
        merchant_isolated = True
        chart_active = False
        chart_stale = False
        chart_fields: set[str] = set()
        chart_basis: MeasurementBasis | None = chart_basis_override
        has_chart_conflict = False
        size_options: list[MerchantSizeOption] = []

        if chart is not None:
            if chart_basis is None:
                chart_basis = MeasurementBasis(chart.measurement_basis.value)
            if merchant_id is not None and str(chart.merchant_id) != str(merchant_id):
                merchant_isolated = False
            if (
                merchant_product_id is not None
                and str(chart.merchant_product_id) != str(merchant_product_id)
            ):
                merchant_isolated = False

            chart_stale = bool(chart.is_stale or chart.status == SizeChartStatus.STALE)
            chart_active = chart.status in (
                SizeChartStatus.AVAILABLE,
                SizeChartStatus.VERIFIED,
            ) and not chart_stale

            if size_options_override is not None:
                size_options = list(size_options_override)
            else:
                size_options, has_chart_conflict = _size_ranges_from_chart(chart, availability)

            for opt in size_options:
                for sr in opt.measurements:
                    chart_fields.add(sr.field)
                    if not sr.valid_range():
                        has_chart_conflict = True
        elif size_options_override is not None:
            # Explicit options override (unit tests where chart metadata is attached)
            size_options = list(size_options_override)
            for opt in size_options:
                for sr in opt.measurements:
                    chart_fields.add(sr.field)
                    if not sr.valid_range():
                        has_chart_conflict = True

        # Shopper measurements: check staleness & extreme chest/waist proportion conflict
        active_shopper = {
            k.strip().upper(): v
            for k, v in shopper_measurements.items()
            if str(v.status).upper() not in ("DELETED", "REVOKED")
        }
        stale_shopper_fields: set[str] = set()
        for fcode, mval in active_shopper.items():
            needs_confirm, _ = evaluate_measurement_freshness(mval.measured_at)
            if needs_confirm or str(mval.status).upper() == "STALE":
                stale_shopper_fields.add(fcode)

        has_shopper_conflict = False
        chest_m = active_shopper.get("CHEST") or active_shopper.get("BUST")
        waist_m = active_shopper.get("WAIST")
        if chest_m and waist_m and waist_m.value_cm > 0:
            ratio = chest_m.value_cm / waist_m.value_cm
            if ratio < Decimal("0.70") or ratio > Decimal("1.80"):
                has_shopper_conflict = True

        required_fields = policy.required_measurements if policy else ()
        optional_fields = policy.optional_measurements if policy else ()
        supported_bases = policy.supported_bases if policy else ()

        # Lookup validated ease rules only when basis == GARMENT
        ease_rules: dict[str, EaseRule] = {}
        has_validated_ease_policy = False
        if chart_basis == MeasurementBasis.GARMENT and policy is not None:
            found_all = True
            for req in required_fields:
                rule = self.ease_registry.get_rule(
                    category=norm_cat,
                    measurement=req,
                    basis=MeasurementBasis.GARMENT,
                    intended_fit=fit_preference,
                )
                if rule is None:
                    found_all = False
                else:
                    ease_rules[req] = rule
            has_validated_ease_policy = found_all and bool(required_fields)

        any_variant_available = any(opt.available for opt in size_options) if size_options else False

        ev_status = validate_evidence(
            category_enabled=category_enabled,
            chart_exists=chart_exists,
            chart_active=chart_active,
            chart_basis=chart_basis,
            supported_bases=supported_bases,
            permissions_valid=permissions_valid,
            required_measurements=required_fields,
            shopper_fields=set(active_shopper.keys()),
            chart_fields=chart_fields,
            chart_stale=chart_stale,
            has_chart_conflict=has_chart_conflict,
            merchant_isolated=merchant_isolated,
            consent_verified=consent_verified,
            stale_shopper_fields=stale_shopper_fields,
            has_shopper_conflict=has_shopper_conflict,
            any_variant_available=any_variant_available if chart_exists else True,
            has_validated_ease_policy=has_validated_ease_policy,
        )

        # Calculate internal evidence score
        req_count = len(required_fields)
        present_req_count = sum(1 for f in required_fields if f in active_shopper)
        compat_count = sum(1 for f in required_fields if f in active_shopper and f in chart_fields)
        dimensions = build_evidence_dimensions(
            required_count=req_count,
            present_shopper_count=present_req_count,
            shopper_fresh=len(stale_shopper_fields & set(required_fields)) == 0,
            chart_present=chart_exists,
            chart_fresh=chart_exists and not chart_stale and chart_active,
            chart_basis_known=chart_basis is not None and chart_basis != MeasurementBasis.UNKNOWN,
            category_enabled=category_enabled,
            compatible_field_count=compat_count,
            variant_available=any_variant_available,
        )
        score = calculate_evidence_score(dimensions)

        decision = recommend_size(
            shopper_measurements=active_shopper,
            sizes=size_options,
            required_fields=required_fields,
            evidence_eligible=ev_status.eligible,
            blocking_status=ev_status.blocking_status,
            blocking_reasons=ev_status.reason_codes,
            optional_fields=optional_fields,
            chart_basis=chart_basis or MeasurementBasis.BODY,
            ease_rules=ease_rules if has_validated_ease_policy else None,
            fit_preference=fit_preference,
            confidence_dimensions=dimensions,
            internal_threshold=internal_threshold,
        )

        reason_codes: list[FitReasonCode | str] = list(decision.reason_codes)
        missing_info: list[MissingDataCode | str] = list(ev_status.missing_information)

        rec_label = (
            decision.recommended_size.merchant_size_label if decision.recommended_size else None
        )
        alt_labels = [a.merchant_size_label for a in decision.alternative_sizes]
        explanations, summary = build_summary_explanation(
            reason_codes=reason_codes,
            recommended_label=rec_label,
            alternative_labels=alt_labels,
        )
        next_actions = build_next_actions(missing_info)

        max_rev = shopper_measurement_revision or max(
            (m.revision for m in active_shopper.values()),
            default=None,
        )

        evidence_summary = FitEvidenceSummary(
            merchant_id=str(merchant_id) if merchant_id else (str(chart.merchant_id) if chart else None),
            merchant_product_id=(
                str(merchant_product_id)
                if merchant_product_id
                else (str(chart.merchant_product_id) if chart else None)
            ),
            merchant_offer_id=str(merchant_offer_id) if merchant_offer_id else None,
            product_id=str(product_id),
            size_chart_id=str(chart.chart_id) if chart else None,
            size_chart_revision=chart.version if chart else None,
            size_system_code=chart.size_system.code if chart else None,
            measurement_basis=chart_basis or MeasurementBasis.UNKNOWN,
            shopper_measurement_revision=max_rev,
            category_policy_version=policy.version if policy else None,
            fit_algorithm_version=FIT_ALGORITHM_VERSION,
            fit_preference_revision=fit_preference_revision,
            fit_preference_applied=fit_preference,
            preference_evaluated=decision.preference_evaluated,
            source_id=chart.provenance.source_id if chart else None,
            source_revision=chart.provenance.source_revision if chart else None,
            source_permission_revision=source_permission_revision,
            taxonomy_version=policy.taxonomy_version if policy else "1.0",
            evidence_items=list(ev_status.evidence_items),
        )

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=30)

        if persist_snapshot:
            ev_records: list[dict[str, Any]] = []
            if active_shopper:
                ev_records.append(
                    {
                        "source_type": "SHOPPER_MEASUREMENT",
                        "source_id": str(shopper_id),
                        "source_revision": str(max_rev or 1),
                        "measurement_basis": "BODY",
                        "evidence_status": "STALE" if stale_shopper_fields else "VALID",
                    }
                )
            if chart is not None:
                ev_records.append(
                    {
                        "source_type": "MERCHANT_SIZE_CHART",
                        "source_id": str(chart.chart_id),
                        "source_revision": str(chart.version),
                        "measurement_basis": (chart_basis or MeasurementBasis.UNKNOWN).value,
                        "evidence_status": chart.status.value,
                    }
                )
            await self.repo.save_recommendation_snapshot(
                recommendation_id=rec_id,
                user_id=shopper_id,
                product_id=product_id,
                merchant_id=evidence_summary.merchant_id,
                merchant_product_id=evidence_summary.merchant_product_id,
                merchant_offer_id=merchant_offer_id,
                variant_id=decision.recommended_size.variant_id if decision.recommended_size else None,
                size_chart_id=evidence_summary.size_chart_id,
                size_chart_revision=evidence_summary.size_chart_revision,
                shopper_measurement_revision=max_rev,
                category_policy_version=evidence_summary.category_policy_version,
                fit_algorithm_version=FIT_ALGORITHM_VERSION,
                fit_preference_revision=fit_preference_revision,
                source_permission_revision=source_permission_revision,
                status=decision.status.value,
                recommended_size=rec_label,
                alternative_sizes=alt_labels,
                reason_codes=[r.value if isinstance(r, FitReasonCode) else str(r) for r in reason_codes],
                internal_confidence_score=score,
                evidence_records=ev_records,
                candidate_records=list(decision.evaluated_candidates),
                expires_at=expires_at,
            )

        return FitRecommendationResult(
            recommendation_id=rec_id,
            status=decision.status,
            recommended_size=decision.recommended_size,
            alternative_sizes=list(decision.alternative_sizes),
            confidence=ConfidenceSummary(
                score=score,
                type=ConfidenceType.INTERNAL_EVIDENCE_SCORE,
                display_to_shopper=False,
            ),
            reason_codes=reason_codes,
            missing_information=missing_info,
            explanations=explanations,
            explanation=summary,
            evidence=evidence_summary,
            is_valid=True,
            fit_guaranteed=False,
            next_actions=next_actions,
            created_at=now,
            expires_at=expires_at,
        )

    async def get_stored_recommendation(
        self,
        *,
        recommendation_id: UUID | str,
        shopper_id: UUID | str,
    ) -> FitRecommendationResult:
        """Retrieve a previously stored recommendation snapshot for the owning shopper."""
        rec = await self.repo.get_recommendation_for_owner(recommendation_id, shopper_id)
        reason_codes: list[FitReasonCode | str] = list(rec.reason_codes_json or [rec.explanation_code])
        status_enum = RecommendationStatus(rec.recommendation_status or rec.outcome)
        rec_detail = (
            RecommendedSizeDetail(
                variant_id=rec.variant_id or f"{rec.product_id}:{rec.recommended_size}",
                merchant_size_label=rec.recommended_size,
            )
            if rec.recommended_size
            else None
        )
        alt_details = [
            RecommendedSizeDetail(
                variant_id=f"{rec.product_id}:{lbl}",
                merchant_size_label=lbl,
            )
            for lbl in (rec.alternative_sizes or [])
        ]
        explanations, summary = build_summary_explanation(
            reason_codes=reason_codes,
            recommended_label=rec.recommended_size,
            alternative_labels=list(rec.alternative_sizes or []),
        )
        basis = MeasurementBasis.UNKNOWN
        for ev in rec.evidence_json or []:
            if ev.get("source_type") == "MERCHANT_SIZE_CHART" and ev.get("measurement_basis"):
                basis = MeasurementBasis(str(ev["measurement_basis"]))

        return FitRecommendationResult(
            recommendation_id=getattr(rec, "_raw_rec_id", str(rec.id)),
            status=status_enum,
            recommended_size=rec_detail,
            alternative_sizes=alt_details,
            confidence=ConfidenceSummary(
                score=rec.internal_confidence_score or Decimal("0.000"),
                type=ConfidenceType.INTERNAL_EVIDENCE_SCORE,
                display_to_shopper=False,
            ),
            reason_codes=reason_codes,
            explanations=explanations,
            explanation=summary,
            evidence=FitEvidenceSummary(
                merchant_id=getattr(rec, "_raw_merchant_id", str(rec.merchant_id) if rec.merchant_id else None),
                merchant_product_id=str(rec.merchant_product_id) if rec.merchant_product_id else None,
                merchant_offer_id=getattr(rec, "_raw_offer_id", str(rec.merchant_offer_id) if rec.merchant_offer_id else None),
                product_id=getattr(rec, "_raw_product_id", str(rec.product_id)),
                size_chart_id=getattr(rec, "_raw_chart_id", str(rec.size_chart_id) if rec.size_chart_id else None),
                size_chart_revision=rec.size_chart_revision,
                measurement_basis=basis,
                shopper_measurement_revision=rec.shopper_measurement_revision,
                category_policy_version=rec.category_policy_version,
                fit_algorithm_version=rec.fit_algorithm_version or rec.fit_model_version,
                fit_preference_revision=rec.fit_preference_revision,
                source_permission_revision=rec.source_permission_revision,
            ),
            is_valid=rec.is_valid,
            invalidated_reason=rec.invalidation_reason,
            fit_guaranteed=False,
            created_at=rec.created_at,
            expires_at=rec.expires_at,
        )

    # -----------------------------------------------------------------------
    # Phase 07.8 Backward-Compatible Method
    # -----------------------------------------------------------------------

    async def recommend(
        self,
        *,
        shopper_measurements: ShopperMeasurementsInput | None,
        size_chart: MerchantSizeChartResponse | None,
        product: FitProductInput,
        fit_model: FitModelSpec | None = None,
        external_evidence: list[EvidenceReference] | None = None,
    ) -> FitRecommendationResponse:
        model = fit_model or FitModelSpec()
        rec_id = f"fitrec_{uuid.uuid4().hex[:12]}"

        reject_prohibited_evidence(external_evidence)

        cat_clean = product.category.strip().lower().replace(" ", "_").replace("-", "_")
        if cat_clean not in model.supported_categories:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.UNSUPPORTED_CATEGORY,
                explanation_code="FIT_CATEGORY_NOT_SUPPORTED",
                explanation_message=f"No validated fit model exists for category '{product.category}'.",
                fit_model_version=model.version,
            )

        if not size_chart:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.INSUFFICIENT_DATA,
                explanation_code="VERIFIED_SIZE_CHART_REQUIRED",
                explanation_message="We do not have enough verified information to recommend a size for this product.",
                fit_model_version=model.version,
            )

        if size_chart.is_stale or size_chart.status == SizeChartStatus.STALE:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.STALE_SIZE_CHART,
                explanation_code="SIZE_CHART_EXPIRED",
                explanation_message="The merchant size chart is outdated. Please inspect the chart manually.",
                fit_model_version=model.version,
                evidence=[
                    EvidenceReference(
                        source_type="MERCHANT_SIZE_CHART",
                        source_id=size_chart.chart_id,
                        source_revision=size_chart.source_revision,
                    )
                ],
            )

        if size_chart.status != SizeChartStatus.VERIFIED:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.INSUFFICIENT_DATA,
                explanation_code="VERIFIED_SIZE_CHART_REQUIRED",
                explanation_message="We do not have enough verified information to recommend a size for this product.",
                fit_model_version=model.version,
            )

        if not shopper_measurements:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.INSUFFICIENT_DATA,
                explanation_code="SHOPPER_MEASUREMENTS_REQUIRED",
                explanation_message="We do not have your body measurements to recommend a size.",
                fit_model_version=model.version,
            )

        if not shopper_measurements.consent_verified:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.INSUFFICIENT_DATA,
                explanation_code="MEASUREMENT_CONSENT_REQUIRED",
                explanation_message="Consent to use body measurements is required for fit prediction.",
                fit_model_version=model.version,
            )

        has_dimensional = any(
            v is not None
            for v in [
                shopper_measurements.chest_cm,
                shopper_measurements.waist_cm,
                shopper_measurements.hip_cm,
                shopper_measurements.shoulder_cm,
            ]
        )
        if not has_dimensional:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.INSUFFICIENT_DATA,
                explanation_code="DIMENSIONAL_MEASUREMENTS_REQUIRED",
                explanation_message="Height and weight alone are insufficient to predict garment fit.",
                fit_model_version=model.version,
            )

        evidence: list[EvidenceReference] = [
            EvidenceReference(
                source_type="SHOPPER_MEASUREMENT",
                source_id=shopper_measurements.user_id,
                source_revision=shopper_measurements.measurement_revision,
            ),
            EvidenceReference(
                source_type="MERCHANT_SIZE_CHART",
                source_id=size_chart.chart_id,
                source_revision=size_chart.source_revision,
            ),
            EvidenceReference(
                source_type="FIT_MODEL_CONFIG",
                source_id=model.model_id,
                source_revision=model.version,
            ),
        ]

        shopper_chest = shopper_measurements.chest_cm
        shopper_waist = shopper_measurements.waist_cm
        if shopper_chest and shopper_waist:
            ratio = shopper_chest / shopper_waist
            if ratio < Decimal("0.70") or ratio > Decimal("1.80"):
                return FitRecommendationResponse(
                    recommendation_id=rec_id,
                    product_id=product.product_id,
                    merchant_offer_id=product.merchant_offer_id,
                    outcome=FitOutcome.CONFLICTING_DATA,
                    explanation_code="MEASUREMENT_PROPORTION_CONFLICT",
                    explanation_message="Shopper body measurements show conflicting proportions.",
                    fit_model_version=model.version,
                    evidence=evidence,
                )

        matching_sizes: list[tuple[str, Decimal]] = []
        is_garment_basis = size_chart.basis == CatalogMeasurementBasis.GARMENT
        ease_chest_min = Decimal("3.0") if is_garment_basis else Decimal("-2.0")
        ease_chest_max = Decimal("9.0") if is_garment_basis else Decimal("3.0")

        for row in size_chart.rows:
            if not row.chest:
                continue
            diff = row.chest - (shopper_chest or Decimal("0"))
            if ease_chest_min <= diff <= ease_chest_max:
                matching_sizes.append((row.merchant_size, abs(diff - Decimal("6.0"))))

        if product.available_sizes:
            matching_sizes = [m for m in matching_sizes if m[0] in product.available_sizes]

        if not matching_sizes:
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.NO_AVAILABLE_SIZE,
                explanation_code="NO_MATCHING_IN_STOCK_SIZE",
                explanation_message="No available size fits within acceptable ease tolerance.",
                fit_model_version=model.version,
                evidence=evidence,
            )

        matching_sizes.sort(key=lambda x: x[1])
        best_size = matching_sizes[0][0]
        if len(matching_sizes) > 1 and matching_sizes[1][1] - matching_sizes[0][1] < Decimal("1.0"):
            alt_sizes = [m[0] for m in matching_sizes[1:3]]
            return FitRecommendationResponse(
                recommendation_id=rec_id,
                product_id=product.product_id,
                merchant_offer_id=product.merchant_offer_id,
                outcome=FitOutcome.POSSIBLE_ALTERNATIVES,
                recommended_size=best_size,
                alternative_sizes=alt_sizes,
                explanation_code="MULTIPLE_PLAUSIBLE_SIZES",
                explanation_message=(
                    f"Size {best_size} or {', '.join(alt_sizes)} may suit depending on fit preference."
                ),
                fit_model_version=model.version,
                evidence=evidence,
            )

        return FitRecommendationResponse(
            recommendation_id=rec_id,
            product_id=product.product_id,
            merchant_offer_id=product.merchant_offer_id,
            outcome=FitOutcome.RECOMMENDED,
            recommended_size=best_size,
            explanation_code="BEST_FIT_MATCH",
            explanation_message=(
                f"Size {best_size} is recommended based on chest measurement and ease tolerance."
            ),
            fit_model_version=model.version,
            evidence=evidence,
        )
