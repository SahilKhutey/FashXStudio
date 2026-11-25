from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from fashx.catalog.size_charts.schemas import (
    MeasurementBasis,
    MerchantSizeChartResponse,
    SizeChartStatus,
)
from fashx.fit.contracts import (
    EvidenceReference,
    FitModelSpec,
    FitOutcome,
    FitProductInput,
    FitRecommendationResponse,
    ShopperMeasurementsInput,
)


class FitEvidenceSecurityError(ValueError):
    """Raised when an illegal evidence type (such as an AI-generated VTO image) is submitted."""

    pass


class FitRecommendationService:
    """Evidence-based fit recommendation engine.

    Strict Invariants:
    1. Visual Try-On outputs CANNOT be consumed as proof or evidence of physical fit.
    2. Missing or unverified size charts fail closed to INSUFFICIENT_DATA.
    3. Height and weight alone without dimensional measurements fail closed.
    4. Fit guarantees are strictly prohibited.
    """

    def __init__(self, session_or_db: Any = None) -> None:
        self.session = session_or_db

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

        # Security check: Prohibit VTO images as fit evidence
        if external_evidence:
            for ev in external_evidence:
                st = ev.source_type.upper()
                if "VTO" in st or "TRYON" in st or "GENERATED" in st or "IMAGE" in st:
                    raise FitEvidenceSecurityError(
                        f"Prohibited fit evidence source type '{ev.source_type}'. "
                        "Virtual try-on images cannot be used as proof of fit."
                    )

        # 1. Category validation
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

        # 2. Size chart verification & freshness
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

        # 3. Shopper measurements & consent
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

        # Invariant: Height and weight alone are insufficient to predict garment dimensions
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

        # 4. Dimension evaluation based on garment category
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

        # Check for conflicting measurements (e.g. chest implies extreme outlier vs waist)
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

        # Match size from chart rows
        matching_sizes: list[tuple[str, Decimal]] = []
        is_garment_basis = size_chart.basis == MeasurementBasis.GARMENT
        # Standard ease allowance for garment measurements vs body measurements
        ease_chest_min = Decimal("3.0") if is_garment_basis else Decimal("-2.0")
        ease_chest_max = Decimal("9.0") if is_garment_basis else Decimal("3.0")

        for row in size_chart.rows:
            if not row.chest:
                continue
            diff = row.chest - (shopper_chest or Decimal("0"))
            if ease_chest_min <= diff <= ease_chest_max:
                matching_sizes.append((row.merchant_size, abs(diff - Decimal("6.0"))))

        # Check in-stock availability constraint if available_sizes provided
        if product.available_sizes:
            matching_sizes = [
                m for m in matching_sizes if m[0] in product.available_sizes
            ]

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

        # Sort by best fit
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
                explanation_message=f"Size {best_size} or {', '.join(alt_sizes)} may suit depending on fit preference.",
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
            explanation_message=f"Size {best_size} is recommended based on chest measurement and ease tolerance.",
            fit_model_version=model.version,
            evidence=evidence,
        )
