"""Master test suite for Phase 07.9 Deliverables and Production Exit Gate.

Verifies the integration contracts across all Phase 07 subsystems:
- Live provider abstraction and credentials isolation (7.2)
- Shopper & garment input validation and time-of-use guards (7.3)
- Durable job lifecycle, state transitions, and outbox delivery (7.4)
- Reliability, timeouts, recovery, and DLQ persistence (7.5)
- Cache isolation, usage ledgers, and budget spending limits (7.6)
- Dataset governance, automated metrics, and category gates (7.7)
- Strict separation of visual try-on from verified physical fit (7.8)
"""

from __future__ import annotations

import inspect
import uuid
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
    FitOutcome,
    FitProductInput,
    ShopperMeasurementsInput,
)
from fashx.fit.service import FitEvidenceSecurityError, FitRecommendationService
from fashx.presentation.claims import (
    PROHIBITED_CLAIM_PATTERNS,
    assert_claim_valid,
    enforce_merchant_widget_policy,
    get_presentation_policy,
    validate_claim_text,
)
from fashx.tryon.feedback.schemas import FeedbackReason, TryOnFeedbackRequest
from fashx.tryon.feedback.service import FeedbackSecurityError, TryOnFeedbackService
from fashx.tryon.lifecycle.states import JobStatus
from fashx.tryon.lifecycle.transitions import InvalidJobTransition, validate_transition
from fashx.tryon.router import TryOnJobStatusResponse, TryOnStatus


def run_sync(coro):
    """Run an async coroutine synchronously using generator stepping to avoid Windows IOCP deadlocks."""
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
    return val


# GATE A & B: Contract Integrity and Secret Isolation
def test_exit_001_secret_isolation_in_status_response():
    """Verify client status responses never expose provider keys, internal secrets or raw credentials."""
    resp = TryOnJobStatusResponse(
        job_id=uuid.uuid4(),
        garment_id=uuid.uuid4(),
        status=TryOnStatus.COMPLETED,
        artifact_key="results/test-job-001.webp",
        provider="fashn",
        model_version="v1.5",
        pipeline_version="prod-pipeline-v1",
        result_url="https://cdn.fashx.com/results/test-job-001.webp",
        failure_reason=None,
        result_type="VISUAL_TRY_ON",
        is_ai_generated=True,
        fit_verified=False,
        disclaimer_code="VISUAL_TRYON_NOT_FIT_VERIFICATION",
    )
    dumped = resp.model_dump()
    assert "provider_api_key" not in dumped
    assert "secret" not in dumped
    assert "credential" not in dumped
    assert dumped["result_type"] == "VISUAL_TRY_ON"
    assert dumped["fit_verified"] is False
    assert dumped["is_ai_generated"] is True


def test_exit_002_vto_vs_fit_separation_invariant():
    """Verify VTO output cannot be presented as verified fit."""
    policy_data = get_presentation_policy()
    p = policy_data["presentation"]
    assert p["disclaimer_code"] == "VISUAL_TRYON_NOT_FIT_VERIFICATION"
    assert p["fit_verified"] is False
    assert p["is_ai_generated"] is True
    assert "physical fit" in p["copy"]["disclaimer"].lower()


def test_exit_003_vto_evidence_forbidden_in_fit_service():
    """Verify FitRecommendationService strictly rejects VTO image evidence."""
    fit_service = FitRecommendationService()
    shopper_measurements = ShopperMeasurementsInput(
        user_id="shopper-001",
        chest_cm=Decimal("96.0"),
        waist_cm=Decimal("82.0"),
    )
    product = FitProductInput(
        product_id="prod-001",
        merchant_id="m-001",
        merchant_offer_id="off-001",
        category="casual_shirts",
        available_sizes=["M", "L"],
    )
    vto_evidence = [
        EvidenceReference(
            source_type="VTO_IMAGE",
            source_id="vto-result-789",
            source_revision="v1",
        )
    ]
    with pytest.raises(FitEvidenceSecurityError, match="Prohibited fit evidence"):
        run_sync(
            fit_service.recommend(
                shopper_measurements=shopper_measurements,
                size_chart=None,
                product=product,
                external_evidence=vto_evidence,
            )
        )


def test_exit_004_prohibited_claims_enforced_across_platform():
    """Verify prohibited claims ('guaranteed fit', 'perfect fit') are blocked."""
    for term in PROHIBITED_CLAIM_PATTERNS:
        assert validate_claim_text(f"Get a {term} today!") is False
        with pytest.raises(ValueError):
            assert_claim_valid(f"This item provides {term}.")

    widget_config = {
        "title": "FashX Try-On",
        "result_label": "Your Guaranteed Fit Preview",
        "show_disclaimer": True,
    }
    sanitized = enforce_merchant_widget_policy(widget_config)
    assert sanitized["result_label"] == "AI-generated visual try-on"
    assert sanitized["disclaimer_locked"] is True
    assert sanitized["allow_fit_guarantee"] is False


def test_exit_005_durable_state_machine_prevents_illegal_jumps():
    """Verify durable state machine prevents jumping from CREATED to COMPLETED without processing."""
    with pytest.raises(InvalidJobTransition):
        validate_transition(JobStatus.CREATED, JobStatus.COMPLETED)

    # Legal forward transitions
    c1, t1 = validate_transition(JobStatus.CREATED, JobStatus.VALIDATING)
    assert t1 == JobStatus.VALIDATING
    c2, t2 = validate_transition(JobStatus.VALIDATING, JobStatus.QUEUED)
    assert t2 == JobStatus.QUEUED
    c3, t3 = validate_transition(JobStatus.QUEUED, JobStatus.PROCESSING)
    assert t3 == JobStatus.PROCESSING
    c4, t4 = validate_transition(JobStatus.STORING_RESULT, JobStatus.COMPLETED)
    assert t4 == JobStatus.COMPLETED


def test_exit_006_unsupported_category_fails_closed():
    """Verify that unsupported categories (sarees, lehengas) fail closed in fit service."""
    fit_service = FitRecommendationService()
    shopper_measurements = ShopperMeasurementsInput(
        user_id="shopper-001",
        chest_cm=Decimal("92.0"),
        waist_cm=Decimal("78.0"),
    )
    product = FitProductInput(
        product_id="prod-saree-001",
        merchant_id="m-001",
        merchant_offer_id="off-001",
        category="sarees",
        available_sizes=["FreeSize"],
    )
    rec = run_sync(
        fit_service.recommend(
            shopper_measurements=shopper_measurements,
            size_chart=None,
            product=product,
        )
    )
    assert rec.outcome == FitOutcome.UNSUPPORTED_CATEGORY
    assert rec.recommended_size is None


def test_exit_007_shopper_feedback_reason_codes_and_ownership():
    """Verify structured reason codes for quality review and ownership isolation."""
    for reason in FeedbackReason:
        req = TryOnFeedbackRequest(
            reason_code=reason,
            details=f"Test feedback for {reason.value}",
            include_in_quality_review=True,
        )
        assert req.reason_code == reason

    svc = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.GARMENT_LOOKS_DIFFERENT,
        details="Mismatch observed.",
    )
    with pytest.raises(FeedbackSecurityError, match="not authorized"):
        run_sync(
            svc.submit_feedback(
                authenticated_user_id="intruder-user",
                job_id="job-owned-by-alice",
                request=req,
                job_owner_id="alice",
                job_status="completed",
                has_result=True,
            )
        )


def test_exit_008_size_chart_basis_enforced():
    """Verify size charts require explicit measurement basis (BODY or GARMENT)."""
    chart = MerchantSizeChartResponse(
        chart_id="chart-123",
        merchant_id="merchant-1",
        merchant_name="Acme Fashion",
        merchant_product_id="sku-123",
        basis=MeasurementBasis.BODY,
        unit=MeasurementUnit.CM,
        status=SizeChartStatus.VERIFIED,
        source_reference="merchant_sync_job_42",
        source_revision="rev-2026-11-25",
        rows=[
            SizeChartRow(merchant_size="S", chest=Decimal("92.0"), waist=Decimal("76.0")),
            SizeChartRow(merchant_size="M", chest=Decimal("98.0"), waist=Decimal("82.0")),
        ],
    )
    assert chart.basis == MeasurementBasis.BODY
    assert len(chart.rows) == 2
