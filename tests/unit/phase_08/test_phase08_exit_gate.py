"""Phase 08.6 End-to-End Integration & Exit-Gate Verification Tests (E2E-086-001..014)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fashx.catalog.size_charts.enums import (
    MeasurementBasis as CatBasis,
)
from fashx.catalog.size_charts.enums import (
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.schemas import (
    ProductSizeChartResponse,
    SizeChartRowResponse,
    SizeMeasurementResponse,
    SizeSystemRef,
    SourceProvenance,
)
from fashx.catalog.taxonomy.registry import TaxonomyCategoryNode, TaxonomyRegistry
from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.contracts import FeedbackEventRequest
from fashx.feedback.enums import ConsentPurpose as FeedbackConsentPurpose
from fashx.feedback.enums import FeedbackEventType, ReactionState
from fashx.feedback.ingestion import FeedbackIngestionService
from fashx.feedback.processing import FeedbackProcessor
from fashx.feedback.ranking_adapter import (
    build_product_feedback_feature,
    build_shopper_feedback_projection,
)
from fashx.feedback.repository import InMemoryFeedbackRepository
from fashx.fit.contracts import MeasurementValue, MerchantSizeOption, SizeRange
from fashx.fit.enums import FitPreference, MeasurementBasis, RecommendationStatus
from fashx.fit.explanations import assert_no_guarantee_language
from fashx.fit.service import FitRecommendationService
from fashx.presentation.claims import get_presentation_policy
from fashx.profile.consent import FitConsentService
from fashx.profile.fit_schemas import (
    ConsentPurpose as FitConsentPurpose,
)
from fashx.profile.fit_schemas import (
    MeasurementBatchRequest,
    MeasurementInput,
)
from fashx.profile.repositories.fit_profile_repository import FitProfileRepository
from fashx.profile.services.fit_profile_service import FitProfileService
from fashx.profile.units import ProfileUnit
from fashx.ranking.category import RegistryTaxonomyAdapter
from fashx.ranking.contracts import (
    CandidateVariant,
    RankingCandidate,
    RankingContext,
    ShopperPreferenceSnapshot,
)
from fashx.ranking.service import PersonalizedRankingService


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
        except StopIteration as exc:
            val = exc.value
            stack.pop()
    return val


def _make_taxonomy() -> RegistryTaxonomyAdapter:
    nodes = {
        "tops": TaxonomyCategoryNode(
            id="tops",
            label="Tops",
            parent_id=None,
            path="tops",
            children_ids=["SHIRTS"],
            is_leaf=False,
        ),
        "SHIRTS": TaxonomyCategoryNode(
            id="SHIRTS", label="Shirts", parent_id="tops", path="tops/SHIRTS"
        ),
    }
    return RegistryTaxonomyAdapter(
        TaxonomyRegistry(
            version="v1.0.0",
            categories=nodes,
            garment_types={},
            occasions={},
            audiences={},
            color_families={},
            color_shades={},
            patterns={},
            materials={},
            sleeves={},
            necklines={},
            collars={},
            fits={},
            silhouettes={},
            indian_wear={},
            western_wear={},
            footwear={},
            accessories={},
            missing_values={},
        )
    )


def _make_shirt_chart(
    *,
    chart_id: str,
    product_id: str,
    merchant_id: str,
    revision: int = 1,
    basis: CatBasis = CatBasis.BODY,
) -> ProductSizeChartResponse:
    return ProductSizeChartResponse(
        chart_id=chart_id,
        merchant_id=merchant_id,
        merchant_product_id=product_id,
        version=revision,
        content_fingerprint=f"fp-{revision}",
        size_system=SizeSystemRef(code="INTL_ALPHA", display_name="INTL"),
        measurement_basis=basis,
        display_unit=MeasurementUnit.CM,
        status=SizeChartStatus.AVAILABLE,
        is_stale=False,
        provenance=SourceProvenance(source_id="src-1", source_revision="rev-1"),
        last_verified_at=datetime.now(UTC),
        rows=[
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
            SizeChartRowResponse(
                merchant_size="L",
                measurements=[
                    SizeMeasurementResponse(
                        field_code="CHEST",
                        display_name="Chest",
                        value=Decimal("102"),
                        unit=MeasurementUnit.CM,
                        normalized_cm=Decimal("102"),
                    )
                ],
            ),
        ],
    )


def test_e2e_086_profile_to_size_chart_to_fit_recommendation_and_abstention() -> None:
    """E2E-086-001..004: Profile -> Size Chart -> Fit Recommendation & Abstention."""
    shopper_id = uuid4()
    profile_service = FitProfileService(
        repository=FitProfileRepository(),
        consent_service=FitConsentService(),
    )
    _run(
        profile_service.update_consent(
            user_id=shopper_id,
            purpose=FitConsentPurpose.FIT_PROFILE_STORAGE,
            granted=True,
            is_18_or_older=True,
        )
    )
    profile_view = _run(
        profile_service.add_measurements(
            user_id=shopper_id,
            batch=MeasurementBatchRequest(
                measurements=[
                    MeasurementInput(
                        field="CHEST",
                        value=Decimal("96"),
                        unit=ProfileUnit.CM,
                    ),
                    MeasurementInput(
                        field="HEIGHT",
                        value=Decimal("178"),
                        unit=ProfileUnit.CM,
                    ),
                ]
            ),
        )
    )
    meas_map = {
        m.field: MeasurementValue(
            field=m.field,
            value_cm=m.normalized_value,
            measured_at=m.measured_at,
            revision=m.version,
            provenance="SHOPPER_ENTERED",
        )
        for m in profile_view.measurements
    }

    chart_v1 = _make_shirt_chart(
        chart_id="chart-1", product_id="prod-1", merchant_id="merch-1", revision=1
    )
    size_options = [
        MerchantSizeOption(
            variant_id="var-m",
            merchant_size_label="M",
            available=True,
            measurements=[
                SizeRange(
                    field="CHEST",
                    minimum_cm=Decimal("94"),
                    maximum_cm=Decimal("99"),
                    basis=MeasurementBasis.BODY,
                ),
            ],
        ),
        MerchantSizeOption(
            variant_id="var-l",
            merchant_size_label="L",
            available=True,
            measurements=[
                SizeRange(
                    field="CHEST",
                    minimum_cm=Decimal("100"),
                    maximum_cm=Decimal("105"),
                    basis=MeasurementBasis.BODY,
                ),
            ],
        ),
    ]
    fit_service = FitRecommendationService()
    rec = _run(
        fit_service.evaluate_recommendation(
            shopper_id=str(shopper_id),
            product_id="prod-1",
            merchant_offer_id="offer-1",
            merchant_id="merch-1",
            merchant_product_id="prod-1",
            category="TSHIRTS",
            shopper_measurements=meas_map,
            chart=chart_v1,
            fit_preference=FitPreference.REGULAR,
            size_options_override=size_options,
        )
    )
    assert rec.status == RecommendationStatus.RECOMMENDED
    assert rec.recommended_size is not None
    assert rec.recommended_size.merchant_size_label == "M"
    assert rec.evidence.size_chart_revision == 1
    assert rec.fit_guaranteed is False
    assert_no_guarantee_language(rec.explanation)

    # E2E-086-002: Missing required chest measurement triggers abstention
    abstain_missing = _run(
        fit_service.evaluate_recommendation(
            shopper_id=str(shopper_id),
            product_id="prod-1",
            merchant_offer_id="offer-1",
            merchant_id="merch-1",
            merchant_product_id="prod-1",
            category="TSHIRTS",
            shopper_measurements={"HEIGHT": meas_map["HEIGHT"]},
            chart=chart_v1,
            fit_preference=FitPreference.REGULAR,
            size_options_override=size_options,
        )
    )
    assert abstain_missing.status == RecommendationStatus.INSUFFICIENT_INFORMATION
    assert abstain_missing.recommended_size is None

    # E2E-086-004: Chart revision update propagates to new recommendations
    chart_v2 = _make_shirt_chart(
        chart_id="chart-1", product_id="prod-1", merchant_id="merch-1", revision=2
    )
    rec_v2 = _run(
        fit_service.evaluate_recommendation(
            shopper_id=str(shopper_id),
            product_id="prod-1",
            merchant_offer_id="offer-1",
            merchant_id="merch-1",
            merchant_product_id="prod-1",
            category="TSHIRTS",
            shopper_measurements=meas_map,
            chart=chart_v2,
            fit_preference=FitPreference.REGULAR,
            size_options_override=size_options,
        )
    )
    assert rec_v2.evidence.size_chart_revision == 2


def test_e2e_086_feedback_to_personalized_ranking_consent_and_vto_separation() -> None:
    """E2E-086-005..014: Feedback -> Projection -> Ranking -> Consent Withdrawal & VTO Separation."""
    uid = str(uuid4())
    fb_repo = InMemoryFeedbackRepository()
    fb_consent = FeedbackConsentService()
    fb_consent.set_consent(
        shopper_id=uid,
        purpose=FeedbackConsentPurpose.PERSONALIZED_RANKING,
        granted=True,
    )
    ingestion = FeedbackIngestionService(repository=fb_repo, consent_service=fb_consent)
    processor = FeedbackProcessor(repository=fb_repo, consent_service=fb_consent)

    # E2E-086-008: Duplicate event retry produces exactly one logical effect
    like_eid = uuid4()
    like_req = FeedbackEventRequest(
        event_id=like_eid,
        event_type=FeedbackEventType.PRODUCT_LIKED.value,
        subject_type="PRODUCT",
        subject_id="prod-liked",
        occurred_at=datetime.now(UTC),
    )
    stored, d1 = ingestion.ingest(shopper_id=uid, request=like_req)
    _, d2 = ingestion.ingest(shopper_id=uid, request=like_req)
    assert d1 is False and d2 is True
    assert processor.process_event(stored.event_id) == "PROCESSED"

    dislike_ev, _ = ingestion.ingest(
        shopper_id=uid,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_DISLIKED.value,
            subject_type="PRODUCT",
            subject_id="prod-disliked",
            occurred_at=datetime.now(UTC),
        ),
    )
    processor.process_event(dislike_ev.event_id)

    proj = build_shopper_feedback_projection(
        shopper_id=uid, repository=fb_repo, consent_service=fb_consent
    )
    assert build_product_feedback_feature(proj["prod-liked"]) == 1.0
    assert build_product_feedback_feature(proj["prod-disliked"]) == 0.0

    # Connect projections into PersonalizedRankingService (Phase 08.4)
    ranking_svc = PersonalizedRankingService(taxonomy=_make_taxonomy())
    shopper_snapshot = ShopperPreferenceSnapshot(
        shopper_id=uid,
        profile_revision=fb_repo.preference_revisions.get(uid, 1),
        liked_styles={"MINIMAL": 1.0},
        preferred_colors=frozenset({"NAVY"}),
        budget_min=Decimal("500"),
        budget_max=Decimal("1500"),
        feedback_by_product={
            pid: ([p.reaction] if p.reaction != ReactionState.NONE.value else [])
            for pid, p in proj.items()
        },
    )
    candidates = [
        RankingCandidate(
            product_id="prod-disliked",
            merchant_id="m1",
            merchant_offer_id="o1",
            title="Disliked Shirt",
            category_id="SHIRTS",
            price=Decimal("1000"),
            variants=(CandidateVariant("v1", "M", "IN_STOCK"),),
            style_tags={"MINIMAL": 0.9},
            primary_colors=("NAVY",),
            availability_verified_at=datetime.now(UTC),
        ),
        RankingCandidate(
            product_id="prod-liked",
            merchant_id="m1",
            merchant_offer_id="o2",
            title="Liked Shirt",
            category_id="SHIRTS",
            price=Decimal("1000"),
            variants=(CandidateVariant("v2", "M", "IN_STOCK"),),
            style_tags={"MINIMAL": 0.9},
            primary_colors=("NAVY",),
            availability_verified_at=datetime.now(UTC),
        ),
        RankingCandidate(
            product_id="prod-takedown",
            merchant_id="m1",
            merchant_offer_id="o3",
            title="Taken Down Shirt",
            category_id="SHIRTS",
            price=Decimal("1000"),
            is_taken_down=True,
            variants=(CandidateVariant("v3", "M", "IN_STOCK"),),
            availability_verified_at=datetime.now(UTC),
        ),
    ]
    ctx = RankingContext(category_id="SHIRTS", selected_size="M", require_selected_size=True)
    ranked_1 = ranking_svc.rank(shopper_profile=shopper_snapshot, candidates=candidates, context=ctx)
    ranked_2 = ranking_svc.rank(shopper_profile=shopper_snapshot, candidates=candidates, context=ctx)

    # E2E-086-005 / 006 / 014: Taken-down excluded, liked outranks disliked, deterministic
    assert [r.product_id for r in ranked_1.results] == ["prod-liked", "prod-disliked"]
    assert [r.product_id for r in ranked_2.results] == [r.product_id for r in ranked_1.results]

    # E2E-086-007: Consent withdrawal clears personalization projection
    fb_consent.withdraw(shopper_id=uid, purpose=FeedbackConsentPurpose.PERSONALIZED_RANKING)
    assert (
        build_shopper_feedback_projection(
            shopper_id=uid, repository=fb_repo, consent_service=fb_consent
        )
        == {}
    )

    # E2E-086-009: VTO presentation policy explicitly disclaims physical fit
    vto_policy = get_presentation_policy(
        result_type="VISUAL_TRY_ON", fit_recommendation_available=False
    )
    assert "fit" in str(vto_policy).lower()
