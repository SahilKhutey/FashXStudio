"""Tests for Evidence Gates, Confidence, Decisions, Merchant Isolation & Explanations (FIT-834..839)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from fashx.catalog.size_charts.enums import (
    AvailabilityStatus,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.enums import (
    MeasurementBasis as CatBasis,
)
from fashx.catalog.size_charts.schemas import (
    ProductSizeChartResponse,
    ProductVariantAvailability,
    SizeChartRowResponse,
    SizeMeasurementResponse,
    SizeSystemRef,
    SourceProvenance,
    VariantStockItem,
)
from fashx.fit.confidence import WEIGHTS, calculate_evidence_score, may_recommend
from fashx.fit.contracts import (
    EvidenceReference,
    MeasurementValue,
    MerchantSizeOption,
    SizeRange,
)
from fashx.fit.ease_policy import EasePolicyRegistry, EaseRule
from fashx.fit.enums import (
    FitPreference,
    FitReasonCode,
    MeasurementBasis,
    MissingDataCode,
    RecommendationStatus,
)
from fashx.fit.evidence import FitEvidenceSecurityError, validate_evidence
from fashx.fit.explanations import assert_no_guarantee_language
from fashx.fit.service import FitRecommendationService


def _run(coro):
    stack = [coro]
    val = None
    while stack:
        curr = stack[-1]
        try:
            if inspect.iscoroutine(curr):
                nxt = curr.send(val)
                val = None
                if inspect.iscoroutine(nxt):
                    stack.append(nxt)
            else:
                stack.pop()
        except StopIteration as e:
            val = e.value
            stack.pop()
        except Exception as exc:
            stack.pop()
            while stack:
                try:
                    nxt = stack[-1].throw(exc)
                    if inspect.iscoroutine(nxt):
                        stack.append(nxt)
                    exc = None
                    break
                except StopIteration as e:
                    val = e.value
                    stack.pop()
                    exc = None
                    break
                except Exception as exc2:
                    exc = exc2
                    stack.pop()
            if exc is not None:
                raise exc
    return val


def _shopper_m(field: str, val: str, *, days_old: int = 1) -> MeasurementValue:
    return MeasurementValue(
        field=field,
        value_cm=Decimal(val),
        measured_at=datetime.now(UTC) - timedelta(days=days_old),
        revision=3,
        provenance="SHOPPER_ENTERED",
    )


def _chart(
    *,
    merchant_id: str = "merch-a",
    merchant_product_id: str = "mp-a-1",
    version: int = 4,
    basis: CatBasis = CatBasis.BODY,
    status: SizeChartStatus = SizeChartStatus.AVAILABLE,
    is_stale: bool = False,
) -> ProductSizeChartResponse:
    return ProductSizeChartResponse(
        chart_id=f"chart-{merchant_id}",
        merchant_product_id=merchant_product_id,
        merchant_id=merchant_id,
        version=version,
        content_fingerprint="abc123",
        size_system=SizeSystemRef(code="INTL_ALPHA", display_name="INTL"),
        measurement_basis=basis,
        display_unit=MeasurementUnit.CM,
        status=status,
        is_stale=is_stale,
        provenance=SourceProvenance(source_id=f"src-{merchant_id}", source_revision="rev-9"),
        rows=[
            SizeChartRowResponse(
                merchant_size="S",
                measurements=[
                    SizeMeasurementResponse(
                        field_code="CHEST",
                        display_name="Chest",
                        value=Decimal("90"),
                        unit=MeasurementUnit.CM,
                        normalized_cm=Decimal("90"),
                    )
                ],
            ),
            SizeChartRowResponse(
                merchant_size="M",
                measurements=[
                    SizeMeasurementResponse(
                        field_code="CHEST",
                        display_name="Chest",
                        value=Decimal("96"),
                        unit=MeasurementUnit.CM,
                        normalized_cm=Decimal("96"),
                    )
                ],
            ),
        ],
        last_verified_at=datetime.now(UTC),
    )


def _body_ranges_options(merchant_product_id: str = "mp-a-1") -> list[MerchantSizeOption]:
    return [
        MerchantSizeOption(
            variant_id=f"{merchant_product_id}:S",
            merchant_size_label="S",
            available=True,
            measurements=[SizeRange(field="CHEST", minimum_cm=Decimal("88"), maximum_cm=Decimal("92"), basis=MeasurementBasis.BODY)],
        ),
        MerchantSizeOption(
            variant_id=f"{merchant_product_id}:M",
            merchant_size_label="M",
            available=True,
            measurements=[SizeRange(field="CHEST", minimum_cm=Decimal("93"), maximum_cm=Decimal("97"), basis=MeasurementBasis.BODY)],
        ),
        MerchantSizeOption(
            variant_id=f"{merchant_product_id}:L",
            merchant_size_label="L",
            available=True,
            measurements=[SizeRange(field="CHEST", minimum_cm=Decimal("98"), maximum_cm=Decimal("102"), basis=MeasurementBasis.BODY)],
        ),
    ]


def test_fit_834_merchant_isolation_and_invalidation() -> None:
    svc = FitRecommendationService()

    # Merchant A recommends M for chest=96
    res_a = _run(
        svc.evaluate_recommendation(
            shopper_id="shopper-1",
            product_id="prod-1",
            merchant_offer_id="off-a",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(merchant_id="merch-a", merchant_product_id="mp-a-1", version=4),
            size_options_override=_body_ranges_options("mp-a-1"),
        )
    )
    assert res_a.status == RecommendationStatus.RECOMMENDED
    assert res_a.recommended_size is not None
    assert res_a.recommended_size.merchant_size_label == "M"
    assert res_a.evidence.merchant_id == "merch-a"
    assert res_a.evidence.size_chart_revision == 4
    assert res_a.confidence.display_to_shopper is False
    assert res_a.fit_guaranteed is False
    assert_no_guarantee_language(res_a.explanation)

    # FIT-834-004: Chart from Merchant B rejected for Merchant A offer (CONFLICTING_DATA)
    wrong_chart = _run(
        svc.evaluate_recommendation(
            shopper_id="shopper-1",
            product_id="prod-1",
            merchant_offer_id="off-a",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(merchant_id="merch-b", merchant_product_id="mp-b-1"),
            size_options_override=_body_ranges_options("mp-b-1"),
        )
    )
    assert wrong_chart.status == RecommendationStatus.CONFLICTING_DATA
    assert wrong_chart.recommended_size is None

    # FIT-834-005: Chart revision change invalidates prior recommendation
    count = _run(svc.repo.invalidate_for_chart("chart-merch-a", reason="SIZE_CHART_CHANGED"))
    assert count >= 1
    stored = _run(
        svc.get_stored_recommendation(
            recommendation_id=res_a.recommendation_id,
            shopper_id="shopper-1",
        )
    )
    assert stored.is_valid is False
    assert stored.invalidated_reason == "SIZE_CHART_CHANGED"


def test_fit_835_and_838_missing_stale_unknown_basis_abstain() -> None:
    svc = FitRecommendationService()

    # FIT-835-001: Missing chest -> abstention (even if height & weight present)
    missing_chest = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={
                "HEIGHT": _shopper_m("HEIGHT", "178"),
                "WEIGHT": _shopper_m("WEIGHT", "72"),
            },
            chart=_chart(),
            size_options_override=_body_ranges_options(),
        )
    )
    assert missing_chest.status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert missing_chest.recommended_size is None
    assert MissingDataCode.SHOPPER_MEASUREMENT_MISSING in missing_chest.missing_information
    assert "CHEST" in missing_chest.missing_information

    # FIT-835-002: Missing merchant chart -> abstention
    missing_chart = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=None,
        )
    )
    assert missing_chart.status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert MissingDataCode.SIZE_CHART_MISSING in missing_chart.missing_information

    # FIT-835-003: Unknown chart basis -> abstention
    unknown_basis = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(basis=CatBasis.UNKNOWN),
            size_options_override=_body_ranges_options(),
        )
    )
    assert unknown_basis.status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert MissingDataCode.MEASUREMENT_BASIS_UNKNOWN in unknown_basis.missing_information

    # FIT-838-003: Stale chart -> STALE_DATA abstention
    stale_chart = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(is_stale=True),
            size_options_override=_body_ranges_options(),
        )
    )
    assert stale_chart.status == RecommendationStatus.STALE_DATA
    assert MissingDataCode.CHART_STALE in stale_chart.missing_information

    # GARMENT basis with no validated EaseRule -> abstention (never invents ease)
    garment_no_ease = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(basis=CatBasis.GARMENT),
            fit_preference=FitPreference.RELAXED,
        )
    )
    assert garment_no_ease.status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert FitReasonCode.EASE_POLICY_MISSING in garment_no_ease.reason_codes

    # FIT-835-005: Optional measurement missing does NOT block recommendation
    # (res_a above had only CHEST, missing SHOULDER/SLEEVE_LENGTH -> still RECOMMENDED)
    assert FitReasonCode.PREFERENCE_NOT_EVALUATED not in missing_chest.reason_codes


def test_fit_836_confidence_dimensions_and_hard_gates() -> None:
    # FIT-836-001..004
    dims = {
        "profile_quality": Decimal("1.0"),
        "chart_quality": Decimal("1.0"),
        "category_quality": Decimal("1.0"),
        "measurement_compatibility": Decimal("1.0"),
        "variant_validity": Decimal("1.0"),
    }
    assert sum(WEIGHTS.values()) == Decimal("1.00")
    score = calculate_evidence_score(dims)
    assert score == Decimal("1.000")
    assert may_recommend(evidence_eligible=True, score=score) is True
    # Hard gate overrides high numerical score!
    assert may_recommend(evidence_eligible=False, score=Decimal("0.990")) is False

    # Missing score dimension raises ValueError
    with pytest.raises(ValueError, match="Incomplete confidence dimensions"):
        calculate_evidence_score({"profile_quality": Decimal("1.0")})

    # Score outside [0, 1] rejected
    bad = dict(dims)
    bad["variant_validity"] = Decimal("1.5")
    with pytest.raises(ValueError, match="out of range"):
        calculate_evidence_score(bad)


def test_fit_837_and_vto_prohibition_and_alternatives() -> None:
    svc = FitRecommendationService()

    # FIT-837-002: Multiple matching sizes return POSSIBLE_ALTERNATIVES rather than guessing
    overlapping = [
        MerchantSizeOption(
            variant_id="mp-a-1:M",
            merchant_size_label="M",
            available=True,
            measurements=[SizeRange(field="CHEST", minimum_cm=Decimal("94"), maximum_cm=Decimal("98"), basis=MeasurementBasis.BODY)],
        ),
        MerchantSizeOption(
            variant_id="mp-a-1:L",
            merchant_size_label="L",
            available=True,
            measurements=[SizeRange(field="CHEST", minimum_cm=Decimal("96"), maximum_cm=Decimal("100"), basis=MeasurementBasis.BODY)],
        ),
    ]
    multi = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "97")},
            chart=_chart(),
            size_options_override=overlapping,
            fit_preference=FitPreference.RELAXED,
        )
    )
    assert multi.status == RecommendationStatus.POSSIBLE_ALTERNATIVES
    assert multi.recommended_size is None
    assert [a.merchant_size_label for a in multi.alternative_sizes] == ["M", "L"]
    assert FitReasonCode.PREFERENCE_NOT_EVALUATED in multi.reason_codes

    # FIT-837-004: All variants OUT_OF_STOCK -> NO_AVAILABLE_SIZE
    oos_avail = ProductVariantAvailability(
        merchant_product_id="mp-a-1",
        overall_status=AvailabilityStatus.OUT_OF_STOCK,
        variants=[
            VariantStockItem(
                variant_id="v-m",
                size_label="M",
                status=AvailabilityStatus.OUT_OF_STOCK,
            )
        ],
    )
    no_var = _run(
        svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(),
            availability=oos_avail,
        )
    )
    assert no_var.status == RecommendationStatus.NO_AVAILABLE_SIZE

    # VTO evidence is strictly rejected
    with pytest.raises(FitEvidenceSecurityError):
        _run(
            svc.evaluate_recommendation(
                shopper_id="s-1",
                product_id="p-1",
                merchant_offer_id="o-1",
                merchant_id="merch-a",
                merchant_product_id="mp-a-1",
                category="TSHIRTS",
                shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
                chart=_chart(),
                external_evidence=[
                    EvidenceReference(
                        source_type="VTO_TRYON_IMAGE",
                        source_id="tryon-1",
                        source_revision="v1",
                    )
                ],
            )
        )

    # FIT-839-003: Prohibited guarantee wording raises ValueError
    with pytest.raises(ValueError, match="Prohibited fit-guarantee language"):
        assert_no_guarantee_language("This shirt is guaranteed to fit your body 100%.")

    # Direct validate_evidence smoke test with EaseRule-equipped GARMENT service
    ease_svc = FitRecommendationService(
        ease_registry=EasePolicyRegistry(
            approved_rules=[
                EaseRule(
                    category="TSHIRTS",
                    measurement="CHEST",
                    basis=MeasurementBasis.GARMENT,
                    intended_fit=FitPreference.RELAXED,
                    garment_construction="COTTON",
                    minimum_cm=Decimal("8"),
                    maximum_cm=Decimal("12"),
                    policy_version="ease-v1",
                    evidence_reference="spec-ref-1",
                )
            ]
        )
    )
    from fashx.fit.category_policy import CategoryFitPolicy

    garment_policy = {
        "TSHIRTS": CategoryFitPolicy(
            category="TSHIRTS",
            taxonomy_version="1.0",
            version="1.0",
            required_measurements=("CHEST",),
            required_chart_measurements=("CHEST",),
            optional_measurements=("SHOULDER",),
            supported_bases=(MeasurementBasis.BODY, MeasurementBasis.GARMENT),
            supported_fit_preferences=(FitPreference.RELAXED, FitPreference.NO_PREFERENCE),
            ease_policy_id="ease-v1",
            enabled=True,
            rationale="Garment ease test policy with validated ease rules.",
        )
    }
    garment_ok = _run(
        ease_svc.evaluate_recommendation(
            shopper_id="s-1",
            product_id="p-1",
            merchant_offer_id="o-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={"CHEST": _shopper_m("CHEST", "96")},
            chart=_chart(basis=CatBasis.GARMENT),
            policy_overrides=garment_policy,
            size_options_override=[
                MerchantSizeOption(
                    variant_id="mp-a-1:M",
                    merchant_size_label="M",
                    available=True,
                    measurements=[
                        SizeRange(
                            field="CHEST",
                            minimum_cm=Decimal("106"),
                            maximum_cm=Decimal("106"),
                            basis=MeasurementBasis.GARMENT,
                        )
                    ],
                )
            ],
            fit_preference=FitPreference.RELAXED,
        )
    )
    assert garment_ok.status == RecommendationStatus.RECOMMENDED
    assert garment_ok.evidence.preference_evaluated is True
    assert validate_evidence(
        category_enabled=True,
        chart_exists=True,
        chart_active=True,
        chart_basis=MeasurementBasis.BODY,
        supported_bases=(MeasurementBasis.BODY,),
        permissions_valid=True,
        required_measurements=("CHEST",),
        shopper_fields={"CHEST"},
        chart_fields={"CHEST"},
    ).eligible is True
