"""Comprehensive unit tests for Phase 08.5 Feedback Loop."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.contracts import FeedbackEventRequest
from fashx.feedback.enums import ConsentPurpose, FeedbackEventType, ReactionState
from fashx.feedback.idempotency import FeedbackConflict, apply_time_decay, validate_occurred_at
from fashx.feedback.ingestion import FeedbackIngestionService
from fashx.feedback.metrics import compute_feedback_monitoring
from fashx.feedback.processing import FeedbackProcessor
from fashx.feedback.ranking_adapter import (
    ProductPreference,
    build_product_feedback_feature,
    build_shopper_feedback_projection,
)
from fashx.feedback.repository import InMemoryFeedbackRepository


def _setup() -> tuple[
    InMemoryFeedbackRepository,
    FeedbackConsentService,
    FeedbackIngestionService,
    FeedbackProcessor,
]:
    repo = InMemoryFeedbackRepository()
    consent = FeedbackConsentService()
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent)
    processor = FeedbackProcessor(repository=repo, consent_service=consent)
    return repo, consent, ingestion, processor


def test_event_idempotency_and_payload_conflict() -> None:
    repo, consent, ingestion, processor = _setup()
    uid = str(uuid4())
    consent.set_consent(
        shopper_id=uid, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True
    )
    eid = uuid4()
    req = FeedbackEventRequest(
        event_id=eid,
        event_type=FeedbackEventType.PRODUCT_LIKED.value,
        subject_type="PRODUCT",
        subject_id="prod-1",
        occurred_at=datetime.now(UTC),
    )

    first, dedup1 = ingestion.ingest(shopper_id=uid, request=req)
    second, dedup2 = ingestion.ingest(shopper_id=uid, request=req)
    assert dedup1 is False
    assert dedup2 is True
    assert first.event_id == second.event_id
    assert repo.count_by_event_id(eid) == 1

    changed = req.model_copy(update={"event_type": FeedbackEventType.PRODUCT_DISLIKED.value})
    with pytest.raises(FeedbackConflict):
        ingestion.ingest(shopper_id=uid, request=changed)

    assert processor.process_event(eid) == "PROCESSED"
    assert processor.process_event(eid) == "ALREADY_PROCESSED"


def test_reactions_and_saved_projections_and_isolation() -> None:
    repo, consent, ingestion, processor = _setup()
    u1, u2 = str(uuid4()), str(uuid4())
    consent.set_consent(shopper_id=u1, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True)
    consent.set_consent(shopper_id=u2, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True)

    e1, _ = ingestion.ingest(
        shopper_id=u1,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_LIKED.value,
            subject_type="PRODUCT",
            subject_id="prod-1",
            occurred_at=datetime.now(UTC),
        ),
    )
    processor.process_event(e1.event_id)
    assert repo.get_reaction(u1, "prod-1") == ReactionState.LIKE
    assert repo.get_reaction(u2, "prod-1") == ReactionState.NONE

    e2, _ = ingestion.ingest(
        shopper_id=u1,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_DISLIKED.value,
            subject_type="PRODUCT",
            subject_id="prod-1",
            occurred_at=datetime.now(UTC),
        ),
    )
    processor.process_event(e2.event_id)
    assert repo.get_reaction(u1, "prod-1") == ReactionState.DISLIKE

    e3, _ = ingestion.ingest(
        shopper_id=u1,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_SAVED.value,
            subject_type="PRODUCT",
            subject_id="prod-2",
            occurred_at=datetime.now(UTC),
        ),
    )
    processor.process_event(e3.event_id)
    saved = repo.get_saved(u1, "prod-2")
    assert saved is not None and saved.is_saved is True

    e4, _ = ingestion.ingest(
        shopper_id=u1,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_UNSAVED.value,
            subject_type="PRODUCT",
            subject_id="prod-2",
            occurred_at=datetime.now(UTC),
        ),
    )
    processor.process_event(e4.event_id)
    saved_after = repo.get_saved(u1, "prod-2")
    assert saved_after is not None and saved_after.is_saved is False


def test_consent_withdrawal_blocks_collection_and_processing() -> None:
    repo, consent, ingestion, processor = _setup()
    uid = str(uuid4())
    consent.set_consent(shopper_id=uid, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True)
    ev, _ = ingestion.ingest(
        shopper_id=uid,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_LIKED.value,
            subject_type="PRODUCT",
            subject_id="prod-1",
            occurred_at=datetime.now(UTC),
        ),
    )
    consent.withdraw(shopper_id=uid, purpose=ConsentPurpose.PERSONALIZED_RANKING)
    assert processor.process_event(ev.event_id) == "SKIPPED"
    assert repo.get_reaction(uid, "prod-1") == ReactionState.NONE
    assert build_shopper_feedback_projection(
        shopper_id=uid, repository=repo, consent_service=consent
    ) == {}

    with pytest.raises(PermissionError):
        ingestion.ingest(
            shopper_id=uid,
            request=FeedbackEventRequest(
                event_id=uuid4(),
                event_type=FeedbackEventType.PRODUCT_CLICKED.value,
                subject_type="PRODUCT",
                subject_id="prod-1",
                occurred_at=datetime.now(UTC),
            ),
        )


def test_server_only_events_vto_failure_and_ranking_adapter() -> None:
    repo, consent, ingestion, processor = _setup()
    uid = str(uuid4())
    consent.set_consent(shopper_id=uid, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True)

    # Client cannot forge server-only VTO_COMPLETED or PURCHASE_CONFIRMED events
    with pytest.raises(PermissionError):
        ingestion.ingest(
            shopper_id=uid,
            request=FeedbackEventRequest(
                event_id=uuid4(),
                event_type=FeedbackEventType.VTO_COMPLETED.value,
                subject_type="VTO_JOB",
                subject_id="job-1",
                occurred_at=datetime.now(UTC),
            ),
        )

    # Authoritative server VTO_FAILED never marks product as DISLIKE
    vto_fail, _ = ingestion.ingest(
        shopper_id=uid,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.VTO_FAILED.value,
            subject_type="VTO_JOB",
            subject_id="job-1",
            occurred_at=datetime.now(UTC),
            context={"product_id": "prod-1"},
        ),
        allow_server_only=True,
    )
    assert processor.process_event(vto_fail.event_id) == "PROCESSED"
    assert repo.get_reaction(uid, "prod-1") == ReactionState.NONE

    assert (
        build_product_feedback_feature(
            ProductPreference(ReactionState.DISLIKE.value, True, 20, 10, None, None)
        )
        == 0.0
    )
    assert (
        build_product_feedback_feature(
            ProductPreference(ReactionState.NONE.value, False, 0, 0, None, None)
        )
        == 0.5
    )


def test_timestamps_time_decay_and_monitoring_metrics() -> None:
    repo, consent, ingestion, processor = _setup()
    uid = str(uuid4())
    consent.set_consent(shopper_id=uid, purpose=ConsentPurpose.PRODUCT_ANALYTICS, granted=True)
    consent.set_consent(shopper_id=uid, purpose=ConsentPurpose.PERSONALIZED_RANKING, granted=True)

    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        validate_occurred_at(now + timedelta(hours=2), now=now)
    assert apply_time_decay(1.0, occurred_at=now - timedelta(days=7), half_life_days=7, now=now) == pytest.approx(0.5)

    imp, _ = ingestion.ingest(
        shopper_id=uid,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_IMPRESSION.value,
            subject_type="PRODUCT",
            subject_id="prod-1",
            occurred_at=now,
        ),
    )
    clk, _ = ingestion.ingest(
        shopper_id=uid,
        request=FeedbackEventRequest(
            event_id=uuid4(),
            event_type=FeedbackEventType.PRODUCT_CLICKED.value,
            subject_type="PRODUCT",
            subject_id="prod-1",
            occurred_at=now,
        ),
    )
    processor.process_event(imp.event_id)
    processor.process_event(clk.event_id)
    metrics = compute_feedback_monitoring(repo)
    assert metrics.impressions_count == 1
    assert metrics.clicks_count == 1
    assert metrics.ctr == 1.0
