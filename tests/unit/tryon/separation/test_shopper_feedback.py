"""Tests for Shopper Try-On Feedback & Quality Review (FDBK-001..015)."""

import pytest

from fashx.tryon.feedback.schemas import (
    FeedbackReason,
    FeedbackReviewStatus,
    FeedbackRootCause,
    FeedbackSeverity,
    TryOnFeedbackRequest,
    TryOnFeedbackReviewAction,
)
from fashx.tryon.feedback.service import (
    FeedbackInvalidJobState,
    FeedbackRateLimitExceeded,
    FeedbackSecurityError,
    TryOnFeedbackService,
)


@pytest.mark.asyncio
async def test_fdbk_001_valid_feedback_submission():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.GARMENT_LOOKS_DIFFERENT,
        details="The generated shirt embroidery is completely missing.",
        include_in_quality_review=True,
    )
    res = await service.submit_feedback(
        authenticated_user_id="user_123",
        job_id="job_001",
        request=req,
        job_owner_id="user_123",
        job_status="completed",
        has_result=True,
    )
    assert res.feedback_id.startswith("fdbk_")
    assert res.status == FeedbackReviewStatus.RECEIVED
    assert res.reason_code == FeedbackReason.GARMENT_LOOKS_DIFFERENT
    assert res.include_in_quality_review is True


def test_fdbk_002_invalid_reason_code_rejected():
    with pytest.raises(Exception):
        TryOnFeedbackRequest(
            reason_code="INVALID_REASON",
            details="Some text",
        )


def test_fdbk_003_excessive_details_rejected():
    long_text = "x" * 2500
    with pytest.raises(Exception):
        TryOnFeedbackRequest(
            reason_code=FeedbackReason.OTHER,
            details=long_text,
        )


@pytest.mark.asyncio
async def test_fdbk_004_non_owner_submission_rejected():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.IMAGE_ARTIFACT,
        details="Artifact on arm",
    )
    with pytest.raises(FeedbackSecurityError, match="not authorized"):
        await service.submit_feedback(
            authenticated_user_id="user_attacker",
            job_id="job_victim",
            request=req,
            job_owner_id="user_victim",
            job_status="completed",
            has_result=True,
        )


@pytest.mark.asyncio
async def test_fdbk_005_duplicate_submission_is_idempotent():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.COLOUR_OR_PATTERN_CHANGED,
        details="Pattern was altered from stripes to solid",
    )
    res1 = await service.submit_feedback(
        authenticated_user_id="user_456",
        job_id="job_002",
        request=req,
        job_owner_id="user_456",
        job_status="completed",
        has_result=True,
    )
    res2 = await service.submit_feedback(
        authenticated_user_id="user_456",
        job_id="job_002",
        request=req,
        job_owner_id="user_456",
        job_status="completed",
        has_result=True,
    )
    assert res1.feedback_id == res2.feedback_id
    assert "already recorded" in res2.message.lower()


@pytest.mark.asyncio
async def test_fdbk_006_report_without_quality_permission():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.MISLEADING_FIT_IMPRESSION,
        details="The output suggests an overly tight fit that does not match size.",
        include_in_quality_review=False,
    )
    res = await service.submit_feedback(
        authenticated_user_id="user_privacy_focused",
        job_id="job_003",
        request=req,
        job_owner_id="user_privacy_focused",
        job_status="completed",
        has_result=True,
    )
    assert res.include_in_quality_review is False


@pytest.mark.asyncio
async def test_fdbk_007_report_with_quality_permission():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.FACE_OR_BODY_CHANGED,
        details="Shopper face identity was altered.",
        include_in_quality_review=True,
    )
    res = await service.submit_feedback(
        authenticated_user_id="user_789",
        job_id="job_004",
        request=req,
        job_owner_id="user_789",
        job_status="completed",
        has_result=True,
    )
    assert res.include_in_quality_review is True


@pytest.mark.asyncio
async def test_fdbk_008_report_for_non_completed_job_rejected():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(reason_code=FeedbackReason.OTHER)
    with pytest.raises(FeedbackInvalidJobState, match="Only completed results can be reported"):
        await service.submit_feedback(
            authenticated_user_id="user_123",
            job_id="job_processing",
            request=req,
            job_owner_id="user_123",
            job_status="processing",
            has_result=False,
        )


@pytest.mark.asyncio
async def test_fdbk_009_cross_tenant_feedback_retrieval_blocked():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(reason_code=FeedbackReason.IMAGE_ARTIFACT)
    res = await service.submit_feedback(
        authenticated_user_id="user_owner",
        job_id="job_owner",
        request=req,
        job_owner_id="user_owner",
        job_status="completed",
        has_result=True,
    )
    with pytest.raises(FeedbackSecurityError, match="cannot access feedback"):
        await service.get_feedback(
            authenticated_user_id="user_intruder",
            feedback_id=res.feedback_id,
        )


def test_fdbk_010_script_tags_in_details_sanitized():
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.OTHER,
        details="Notice this <script>alert('xss')</script> defect",
    )
    assert "<script>" not in req.details
    assert "alert" in req.details


@pytest.mark.asyncio
async def test_fdbk_011_critical_severity_escalates_category():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.FACE_OR_BODY_CHANGED,
        details="Severe identity distortion",
        include_in_quality_review=True,
    )
    sub = await service.submit_feedback(
        authenticated_user_id="user_eval_1",
        job_id="job_eval_1",
        request=req,
        job_owner_id="user_eval_1",
        job_status="completed",
        has_result=True,
    )
    action = TryOnFeedbackReviewAction(
        reviewer_id="reviewer_007",
        review_status=FeedbackReviewStatus.CONFIRMED,
        root_cause=FeedbackRootCause.IDENTITY_PRESERVATION,
        severity=FeedbackSeverity.CRITICAL,
        resolution_notes="Critical facial alteration detected in production render.",
    )
    review_res = await service.review_feedback(
        feedback_id=sub.feedback_id,
        action=action,
    )
    assert review_res["status"] == FeedbackReviewStatus.CONFIRMED
    assert review_res["category_escalated"] is True
    assert review_res["evaluation_candidate_created"] is True


@pytest.mark.asyncio
async def test_fdbk_012_confirmed_with_quality_permission_creates_evaluation_candidate():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.GARMENT_LENGTH_OR_SHAPE,
        include_in_quality_review=True,
    )
    sub = await service.submit_feedback(
        authenticated_user_id="user_eval_2",
        job_id="job_eval_2",
        request=req,
        job_owner_id="user_eval_2",
        job_status="completed",
        has_result=True,
    )
    action = TryOnFeedbackReviewAction(
        reviewer_id="reviewer_008",
        review_status=FeedbackReviewStatus.CONFIRMED,
        root_cause=FeedbackRootCause.GARMENT_PRESERVATION,
        severity=FeedbackSeverity.MEDIUM,
    )
    review_res = await service.review_feedback(feedback_id=sub.feedback_id, action=action)
    assert review_res["evaluation_candidate_created"] is True


@pytest.mark.asyncio
async def test_fdbk_013_confirmed_without_quality_permission_does_not_create_candidate():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(
        reason_code=FeedbackReason.LAYERING_ERROR,
        include_in_quality_review=False,  # Shopper opted out of quality review
    )
    sub = await service.submit_feedback(
        authenticated_user_id="user_eval_3",
        job_id="job_eval_3",
        request=req,
        job_owner_id="user_eval_3",
        job_status="completed",
        has_result=True,
    )
    action = TryOnFeedbackReviewAction(
        reviewer_id="reviewer_008",
        review_status=FeedbackReviewStatus.CONFIRMED,
        root_cause=FeedbackRootCause.LAYERING,
        severity=FeedbackSeverity.LOW,
    )
    review_res = await service.review_feedback(feedback_id=sub.feedback_id, action=action)
    assert review_res["evaluation_candidate_created"] is False
    assert review_res["quality_review_permitted"] is False


@pytest.mark.asyncio
async def test_fdbk_014_rate_limit_exceeded_blocks_submissions():
    service = TryOnFeedbackService()
    user_id = "user_spammer"
    req = TryOnFeedbackRequest(reason_code=FeedbackReason.OTHER)

    # First 5 submissions succeed
    for i in range(5):
        await service.submit_feedback(
            authenticated_user_id=user_id,
            job_id=f"job_burst_{i}",
            request=req,
            job_owner_id=user_id,
            job_status="completed",
            has_result=True,
        )

    # 6th submission in window raises FeedbackRateLimitExceeded
    with pytest.raises(FeedbackRateLimitExceeded, match="Rate limit exceeded"):
        await service.submit_feedback(
            authenticated_user_id=user_id,
            job_id="job_burst_6",
            request=req,
            job_owner_id=user_id,
            job_status="completed",
            has_result=True,
        )


@pytest.mark.asyncio
async def test_fdbk_015_submitting_feedback_does_not_alter_vto_job_status():
    service = TryOnFeedbackService()
    req = TryOnFeedbackRequest(reason_code=FeedbackReason.IMAGE_ARTIFACT)
    res = await service.submit_feedback(
        authenticated_user_id="user_stable",
        job_id="job_stable",
        request=req,
        job_owner_id="user_stable",
        job_status="completed",
        has_result=True,
    )
    # Submission returns feedback receipt without mutating VTO job state
    assert res.job_id == "job_stable"
    assert res.status == FeedbackReviewStatus.RECEIVED
