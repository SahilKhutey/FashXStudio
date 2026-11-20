from __future__ import annotations

import pytest

from fashx.catalog.enrichment.review_service import (
    ReviewAction,
    ReviewPermissionError,
    ReviewService,
    ReviewStatusState,
)
from fashx.catalog.taxonomy.loader import get_taxonomy_registry


def test_enr_028_reviewer_approves_attribute() -> None:
    """Verify ENR-028: Authorized reviewer approves attribute, recording audit event."""
    svc = ReviewService()
    task = svc.create_review_task(
        product_id="prod-1",
        merchant_id="merch-a",
        attribute_id="color",
        proposed_value="navy",
        current_value=None,
        confidence=0.78,
        flags=["LOW_CONFIDENCE"],
    )

    approved = svc.approve_attribute(
        review_id=task.id,
        actor_id="user-rev-1",
        actor_role="PLATFORM_REVIEWER",
        reason="Visual confirmation matches navy",
    )
    assert approved.status == ReviewStatusState.APPROVED
    assert approved.current_value == "navy"
    assert approved.reviewed_by == "user-rev-1"

    events = svc.repo.list_events(task.id)
    assert len(events) == 1
    assert events[0].action == ReviewAction.APPROVE
    assert events[0].new_value == "navy"


def test_enr_029_reviewer_corrects_attribute() -> None:
    """Verify ENR-029: Reviewer corrects value to valid taxonomy term, preserving audit history."""
    svc = ReviewService()
    reg = get_taxonomy_registry()

    task = svc.create_review_task(
        product_id="prod-2",
        merchant_id="merch-a",
        attribute_id="color",
        proposed_value="darkish_blue",
        current_value=None,
        confidence=0.65,
        flags=["LOW_CONFIDENCE"],
    )

    corrected = svc.correct_attribute(
        review_id=task.id,
        corrected_value="navy",
        registry=reg,
        actor_id="user-rev-1",
        actor_role="PLATFORM_REVIEWER",
        reason="Standardized to canonical navy",
    )
    assert corrected.status == ReviewStatusState.CORRECTED
    assert corrected.current_value == "navy"

    events = svc.repo.list_events(task.id)
    assert len(events) == 1
    assert events[0].action == ReviewAction.CORRECT
    assert events[0].new_value == "navy"


def test_enr_030_reviewer_rejects_attribute() -> None:
    """Verify ENR-030: Reviewer rejects false prediction, preventing publishing."""
    svc = ReviewService()
    task = svc.create_review_task(
        product_id="prod-3",
        merchant_id="merch-a",
        attribute_id="fabric",
        proposed_value="silk",
        current_value=None,
        confidence=0.55,
        flags=["LOW_CONFIDENCE", "FABRIC_UNVERIFIED"],
    )

    rejected = svc.reject_attribute(
        review_id=task.id,
        actor_id="user-rev-1",
        actor_role="PLATFORM_REVIEWER",
        reason="Product is actually polyester",
    )
    assert rejected.status == ReviewStatusState.REJECTED
    assert rejected.current_value is None

    events = svc.repo.list_events(task.id)
    assert len(events) == 1
    assert events[0].action == ReviewAction.REJECT


def test_enr_031_cross_merchant_review_access_denied() -> None:
    """Verify ENR-031: Merchant reviewer cannot view or decide reviews of another merchant."""
    svc = ReviewService()
    task = svc.create_review_task(
        product_id="prod-4",
        merchant_id="merch-a",
        attribute_id="fit_type",
        proposed_value="slim",
        current_value=None,
        confidence=0.72,
        flags=["LOW_CONFIDENCE"],
    )

    # Actor from merch-b attempts to approve merch-a product
    with pytest.raises(ReviewPermissionError, match="Access denied: Merchant 'merch-b' cannot review product belonging to 'merch-a'"):
        svc.approve_attribute(
            review_id=task.id,
            actor_id="user-merch-b",
            actor_role="MERCHANT_REVIEWER",
            actor_merchant_id="merch-b",
        )
