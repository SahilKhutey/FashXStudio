"""Tests for Fit Evaluation Dataset, Accuracy/Calibration Metrics & Feedback (FIT-8310..8312)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from fashx.fit.contracts import (
    FitFeedbackCreateRequest,
    FitFeedbackReviewRequest,
    MeasurementValue,
)
from fashx.fit.enums import (
    EvaluationLabel,
    EvaluationSplit,
    FeedbackReviewStatus,
    FitFeedbackReason,
    MeasurementBasis,
    PurchaseStatus,
    RecommendationStatus,
)
from fashx.fit.evaluation import (
    EvaluationCase,
    EvaluationDatasetCase,
    EvaluationDatasetError,
    build_evaluation_report,
    evaluate_cases,
    load_dataset_json,
    validate_dataset_splits,
)
from fashx.fit.feedback import FitFeedbackService
from fashx.fit.repository import DuplicateFitFeedbackError
from fashx.fit.service import FitRecommendationService

FIXTURE_DATASET = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "fit_evaluation"
    / "fixture_cases.json"
)


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


def test_fit_8310_dataset_loading_and_split_leakage_guard() -> None:
    cases = load_dataset_json(FIXTURE_DATASET)
    assert len(cases) == 3
    assert any(c.merchant_id == "merch_heldout" and c.split == EvaluationSplit.TEST for c in cases)

    # Shopper leakage across DEV & TEST raises EvaluationDatasetError
    now = datetime.now(UTC)
    leaked = [
        EvaluationDatasetCase(
            case_id="C1",
            dataset_version="v1",
            split=EvaluationSplit.DEVELOPMENT,
            shopper_key="same_shopper",
            merchant_id="m1",
            product_id="p1",
            merchant_offer_id="o1",
            category="TSHIRTS",
            variant_id="v1",
            size_chart_revision=1,
            measurement_basis=MeasurementBasis.BODY,
            expected_label=EvaluationLabel.RECOMMENDED_SIZE,
            expected_size="M",
            acceptable_sizes=("M",),
            reviewer_id="rev-1",
            labelled_at=now,
            evidence_reference="ref-1",
        ),
        EvaluationDatasetCase(
            case_id="C2",
            dataset_version="v1",
            split=EvaluationSplit.TEST,
            shopper_key="same_shopper",
            merchant_id="m2",
            product_id="p2",
            merchant_offer_id="o2",
            category="TSHIRTS",
            variant_id="v2",
            size_chart_revision=1,
            measurement_basis=MeasurementBasis.BODY,
            expected_label=EvaluationLabel.RECOMMENDED_SIZE,
            expected_size="L",
            acceptable_sizes=("L",),
            reviewer_id="rev-1",
            labelled_at=now,
            evidence_reference="ref-2",
        ),
    ]
    with pytest.raises(EvaluationDatasetError, match="Shopper leakage"):
        validate_dataset_splits(leaked)


def test_fit_8311_metrics_calibration_and_release_gates() -> None:
    # FIT-8311-003: Empty dataset rejected
    with pytest.raises(ValueError, match="Evaluation dataset is empty"):
        evaluate_cases([])

    cases = [
        EvaluationCase(
            expected_size="M",
            predicted_size="M",
            expected_abstention=False,
            predicted_abstention=False,
            acceptable_sizes=("M",),
            category="TSHIRTS",
            merchant_id="merch_a",
            confidence_score=0.92,
        ),
        EvaluationCase(
            expected_size="L",
            predicted_size="L",
            expected_abstention=False,
            predicted_abstention=False,
            acceptable_sizes=("L",),
            category="TSHIRTS",
            merchant_id="merch_a",
            confidence_score=0.84,
        ),
        EvaluationCase(
            expected_size=None,
            predicted_size=None,
            expected_abstention=True,
            predicted_abstention=True,
            expected_label=EvaluationLabel.NO_MATCH,
            predicted_status=RecommendationStatus.NO_AVAILABLE_SIZE,
            category="TSHIRTS",
            merchant_id="merch_heldout",
            confidence_score=None,
        ),
    ]
    summary = evaluate_cases(cases)
    assert summary["total_cases"] == 3
    assert summary["recommendations_made"] == 2
    assert summary["abstentions_made"] == 1
    assert summary["exact_size_accuracy"] == 1.0
    assert summary["acceptable_size_accuracy"] == 1.0
    assert summary["false_recommendation_rate"] == 0.0
    assert summary["coverage"] == 0.6667
    assert summary["abstention_rate"] == 0.3333
    assert summary["small_sample_warning"] is True
    assert summary["calibration_demonstrated"] is False
    assert len(summary["calibration_bins"]) == 2  # type: ignore[arg-type]
    assert "merch_a" in summary["merchant_breakdown"]  # type: ignore[operator]
    assert "merch_heldout" in summary["merchant_breakdown"]  # type: ignore[operator]

    report = build_evaluation_report(
        dataset_version="fixture-v1",
        fit_algorithm_version="08.3.1",
        category_policy_version="1.0",
        cases=cases,
    )
    assert report.all_gates_passed is True


def test_fit_8312_feedback_ownership_dedup_unverified_triage_deletion() -> None:
    svc = FitRecommendationService()
    fb_svc = FitFeedbackService(svc.repo)

    # Create a snapshot owned by shopper-a
    rec = _run(
        svc.evaluate_recommendation(
            shopper_id="shopper-a",
            product_id="prod-1",
            merchant_offer_id="off-1",
            merchant_id="merch-a",
            merchant_product_id="mp-a-1",
            category="TSHIRTS",
            shopper_measurements={
                "CHEST": MeasurementValue(
                    field="CHEST",
                    value_cm=Decimal("95"),
                    measured_at=datetime.now(UTC),
                    revision=1,
                )
            },
            size_options_override=[],
            chart=None,
        )
    )

    # FIT-8312-002: Wrong shopper denied
    with pytest.raises(PermissionError):
        _run(
            fb_svc.submit(
                shopper_id="shopper-b",
                recommendation_id=rec.recommendation_id,
                payload=FitFeedbackCreateRequest(reason=FitFeedbackReason.FIT_TOO_TIGHT),
            )
        )

    # FIT-8312-005: Missing recommendation raises KeyError
    with pytest.raises(KeyError):
        _run(
            fb_svc.submit(
                shopper_id="shopper-a",
                recommendation_id="does-not-exist",
                payload=FitFeedbackCreateRequest(reason=FitFeedbackReason.FIT_TOO_TIGHT),
            )
        )

    # FIT-8312-006: Without physical try-on, recorded as UNVERIFIED
    saved = _run(
        fb_svc.submit(
            shopper_id="shopper-a",
            recommendation_id=rec.recommendation_id,
            payload=FitFeedbackCreateRequest(
                reason=FitFeedbackReason.RECOMMENDATION_UNHELPFUL,
                purchase_status=PurchaseStatus.NOT_PURCHASED,
                tried_on=False,
                comment="Chart link was clear.",
            ),
        )
    )
    assert saved.feedback_basis == "RECOMMENDATION_ONLY"
    assert saved.review_status == FeedbackReviewStatus.UNVERIFIED
    assert saved.product_id == "prod-1"

    # FIT-8312-004: Duplicate feedback rejected
    with pytest.raises(DuplicateFitFeedbackError):
        _run(
            fb_svc.submit(
                shopper_id="shopper-a",
                recommendation_id=rec.recommendation_id,
                payload=FitFeedbackCreateRequest(reason=FitFeedbackReason.FIT_TOO_TIGHT),
            )
        )

    # Triage updates review status without mutating fit rules
    triaged = _run(
        fb_svc.triage_feedback(
            feedback_id=saved.feedback_id,
            review=FitFeedbackReviewRequest(review_status=FeedbackReviewStatus.CLASSIFIED),
        )
    )
    assert triaged.review_status == FeedbackReviewStatus.CLASSIFIED

    # FIT-8312-007: Shopper deletion hides feedback cleanly
    deleted = _run(fb_svc.delete_feedback(shopper_id="shopper-a", feedback_id=saved.feedback_id))
    assert deleted is True
    with pytest.raises(KeyError):
        _run(fb_svc.get_own_feedback(shopper_id="shopper-a", recommendation_id=rec.recommendation_id))
