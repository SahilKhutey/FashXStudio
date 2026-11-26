"""Tests for Fit Recommendation Engine (FIT-001..018)."""

from decimal import Decimal

import pytest

from fashx.catalog.size_charts.schemas import (
    MeasurementBasis,
    MeasurementUnit,
    MerchantSizeChartResponse,
    SizeChartRow,
    SizeChartStatus,
)
from fashx.fit.contracts import (
    EvidenceReference,
    FitModelSpec,
    FitOutcome,
    FitProductInput,
    ShopperMeasurementsInput,
)
from fashx.fit.service import (
    FitEvidenceSecurityError,
    FitRecommendationService,
)


def get_sample_product():
    return FitProductInput(
        product_id="prod_001",
        merchant_id="m_001",
        merchant_offer_id="off_001",
        category="casual_shirts",
        available_sizes=["S", "M", "L", "XL"],
    )


def get_sample_verified_chart():
    rows = [
        SizeChartRow(merchant_size="S", chest=Decimal("94.0")),
        SizeChartRow(merchant_size="M", chest=Decimal("100.0")),
        SizeChartRow(merchant_size="L", chest=Decimal("106.0")),
        SizeChartRow(merchant_size="XL", chest=Decimal("112.0")),
    ]
    return MerchantSizeChartResponse(
        chart_id="sc_001",
        merchant_id="m_001",
        merchant_name="FabIndia",
        merchant_product_id="prod_001",
        basis=MeasurementBasis.GARMENT,
        unit=MeasurementUnit.CM,
        status=SizeChartStatus.VERIFIED,
        is_stale=False,
        source_reference="feed_sync_1",
        source_revision="v1",
        rows=rows,
    )


def get_sample_shopper():
    return ShopperMeasurementsInput(
        user_id="user_123",
        chest_cm=Decimal("94.0"),
        waist_cm=Decimal("80.0"),
        height_cm=Decimal("175.0"),
        weight_kg=Decimal("70.0"),
        consent_verified=True,
    )


@pytest.mark.asyncio
async def test_fit_001_supported_category_produces_recommendation():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    # Shopper chest 94cm + 6cm ease = 100cm garment chest -> Size M
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.RECOMMENDED
    assert res.recommended_size == "M"
    assert res.fit_guaranteed is False
    assert len(res.evidence) >= 2


@pytest.mark.asyncio
async def test_fit_002_missing_shopper_measurements_insufficient_data():
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    res = await service.recommend(
        shopper_measurements=None,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.INSUFFICIENT_DATA
    assert res.recommended_size is None
    assert res.explanation_code == "SHOPPER_MEASUREMENTS_REQUIRED"


@pytest.mark.asyncio
async def test_fit_003_missing_size_chart_insufficient_data():
    shopper = get_sample_shopper()
    product = get_sample_product()
    service = FitRecommendationService()
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=None,
        product=product,
    )
    assert res.outcome == FitOutcome.INSUFFICIENT_DATA
    assert res.recommended_size is None
    assert res.explanation_code == "VERIFIED_SIZE_CHART_REQUIRED"


@pytest.mark.asyncio
async def test_fit_004_unverified_size_chart_blocks_recommendation():
    shopper = get_sample_shopper()
    product = get_sample_product()
    service = FitRecommendationService()
    unverified_chart = get_sample_verified_chart().model_copy(update={"status": SizeChartStatus.UNVERIFIED})
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=unverified_chart,
        product=product,
    )
    assert res.outcome == FitOutcome.INSUFFICIENT_DATA
    assert res.explanation_code == "VERIFIED_SIZE_CHART_REQUIRED"


@pytest.mark.asyncio
async def test_fit_005_stale_size_chart_returns_stale_state():
    shopper = get_sample_shopper()
    product = get_sample_product()
    service = FitRecommendationService()
    stale_chart = get_sample_verified_chart().model_copy(
        update={"status": SizeChartStatus.STALE, "is_stale": True}
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=stale_chart,
        product=product,
    )
    assert res.outcome == FitOutcome.STALE_SIZE_CHART
    assert res.recommended_size is None
    assert res.explanation_code == "SIZE_CHART_EXPIRED"


@pytest.mark.asyncio
async def test_fit_006_unsupported_category_fails_closed():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    service = FitRecommendationService()
    ethnic_product = FitProductInput(
        product_id="prod_saree_01",
        merchant_id="m_001",
        merchant_offer_id="off_saree_01",
        category="sarees",  # Sarees have no validated single-size 2D fit formula
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=ethnic_product,
    )
    assert res.outcome == FitOutcome.UNSUPPORTED_CATEGORY
    assert res.recommended_size is None
    assert res.explanation_code == "FIT_CATEGORY_NOT_SUPPORTED"


@pytest.mark.asyncio
async def test_fit_007_height_and_weight_alone_insufficient():
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    shopper_no_dimensions = ShopperMeasurementsInput(
        user_id="user_hw_only",
        chest_cm=None,
        waist_cm=None,
        height_cm=Decimal("180.0"),
        weight_kg=Decimal("75.0"),
        consent_verified=True,
    )
    res = await service.recommend(
        shopper_measurements=shopper_no_dimensions,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.INSUFFICIENT_DATA
    assert res.explanation_code == "DIMENSIONAL_MEASUREMENTS_REQUIRED"


@pytest.mark.asyncio
async def test_fit_008_conflicting_measurements_returns_conflict():
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    shopper_conflicted = ShopperMeasurementsInput(
        user_id="user_conflicted",
        chest_cm=Decimal("120.0"),  # Outlier chest vs waist ratio > 1.80
        waist_cm=Decimal("60.0"),
        consent_verified=True,
    )
    res = await service.recommend(
        shopper_measurements=shopper_conflicted,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.CONFLICTING_DATA
    assert res.explanation_code == "MEASUREMENT_PROPORTION_CONFLICT"


@pytest.mark.asyncio
async def test_fit_009_no_available_size_returns_no_size():
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    shopper_extra_large = ShopperMeasurementsInput(
        user_id="user_xxxl",
        chest_cm=Decimal("140.0"),  # Far exceeds XL (112cm)
        waist_cm=Decimal("120.0"),
        consent_verified=True,
    )
    res = await service.recommend(
        shopper_measurements=shopper_extra_large,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.NO_AVAILABLE_SIZE
    assert res.recommended_size is None


@pytest.mark.asyncio
async def test_fit_010_multiple_plausible_sizes_returns_alternatives():
    product = get_sample_product()
    service = FitRecommendationService()
    # Close spacing between sizes M (99.5cm) and L (100.5cm)
    tight_chart = MerchantSizeChartResponse(
        chart_id="sc_tight",
        merchant_id="m_001",
        merchant_name="BrandTight",
        merchant_product_id="prod_001",
        basis=MeasurementBasis.GARMENT,
        unit=MeasurementUnit.CM,
        status=SizeChartStatus.VERIFIED,
        is_stale=False,
        source_reference="feed",
        source_revision="v1",
        rows=[
            SizeChartRow(merchant_size="M", chest=Decimal("99.5")),
            SizeChartRow(merchant_size="L", chest=Decimal("100.5")),
        ],
    )
    shopper = ShopperMeasurementsInput(
        user_id="user_between",
        chest_cm=Decimal("94.0"),  # Ideal 100cm
        consent_verified=True,
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=tight_chart,
        product=product,
    )
    assert res.outcome == FitOutcome.POSSIBLE_ALTERNATIVES
    assert res.recommended_size is not None
    assert len(res.alternative_sizes) >= 1


@pytest.mark.asyncio
async def test_fit_011_vto_image_supplied_as_evidence_strictly_rejected():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    illegal_evidence = [
        EvidenceReference(
            source_type="VTO_GENERATED_IMAGE_ARTIFACT",
            source_id="artifact_123",
            source_revision="sha256_abcdef",
        )
    ]
    with pytest.raises(FitEvidenceSecurityError, match="Prohibited fit evidence source type"):
        await service.recommend(
            shopper_measurements=shopper,
            size_chart=chart,
            product=product,
            external_evidence=illegal_evidence,
        )


@pytest.mark.asyncio
async def test_fit_012_unconsented_measurements_blocked():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    unconsented_shopper = shopper.model_copy(update={"consent_verified": False})
    res = await service.recommend(
        shopper_measurements=unconsented_shopper,
        size_chart=chart,
        product=product,
    )
    assert res.outcome == FitOutcome.INSUFFICIENT_DATA
    assert res.explanation_code == "MEASUREMENT_CONSENT_REQUIRED"


@pytest.mark.asyncio
async def test_fit_013_out_of_stock_size_excluded():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    service = FitRecommendationService()
    # Only size S is in stock, but shopper needs M (100cm)
    limited_product = FitProductInput(
        product_id="prod_001",
        merchant_id="m_001",
        merchant_offer_id="off_001",
        category="casual_shirts",
        available_sizes=["S"],
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=limited_product,
    )
    assert res.outcome == FitOutcome.NO_AVAILABLE_SIZE


@pytest.mark.asyncio
async def test_fit_014_fit_guaranteed_is_always_false():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=product,
    )
    assert res.fit_guaranteed is False


@pytest.mark.asyncio
async def test_fit_015_traceable_evidence_structure():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=product,
    )
    source_types = [e.source_type for e in res.evidence]
    assert "SHOPPER_MEASUREMENT" in source_types
    assert "MERCHANT_SIZE_CHART" in source_types
    assert "FIT_MODEL_CONFIG" in source_types


@pytest.mark.asyncio
async def test_fit_016_body_basis_matching():
    product = get_sample_product()
    service = FitRecommendationService()
    body_chart = MerchantSizeChartResponse(
        chart_id="sc_body_01",
        merchant_id="m_001",
        merchant_name="BrandBody",
        merchant_product_id="prod_001",
        basis=MeasurementBasis.BODY,  # Body measurement basis has tighter tolerance
        unit=MeasurementUnit.CM,
        status=SizeChartStatus.VERIFIED,
        is_stale=False,
        source_reference="feed",
        source_revision="v1",
        rows=[
            SizeChartRow(merchant_size="M", chest=Decimal("94.0")),
            SizeChartRow(merchant_size="L", chest=Decimal("100.0")),
        ],
    )
    shopper = ShopperMeasurementsInput(
        user_id="user_body_match",
        chest_cm=Decimal("94.0"),
        consent_verified=True,
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=body_chart,
        product=product,
    )
    assert res.outcome == FitOutcome.RECOMMENDED
    assert res.recommended_size == "M"


@pytest.mark.asyncio
async def test_fit_017_custom_fit_model_spec():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    custom_model = FitModelSpec(
        model_id="custom-fit-v2",
        version="v2.0-beta",
        supported_categories=["casual_shirts"],
    )
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=product,
        fit_model=custom_model,
    )
    assert res.fit_model_version == "v2.0-beta"


@pytest.mark.asyncio
async def test_fit_018_disclaimer_present_in_response():
    shopper = get_sample_shopper()
    chart = get_sample_verified_chart()
    product = get_sample_product()
    service = FitRecommendationService()
    res = await service.recommend(
        shopper_measurements=shopper,
        size_chart=chart,
        product=product,
    )
    assert "not a guarantee of fit" in res.disclaimer.lower()
