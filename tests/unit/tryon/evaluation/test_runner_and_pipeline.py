"""Unit tests for TryOnEvaluationRunner and benchmark metrics (Phase 07.7).

Covers EVAL-001 through EVAL-012.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from backend.fashx.tryon.evaluation.contracts import (
    EvaluationPair,
    EvaluationRunConfig,
    ExpectedOutcome,
)
from backend.fashx.tryon.evaluation.runner import (
    EvaluationItemResult,
    TryOnEvaluationRunner,
)

SAMPLE_RUN_CONFIG = EvaluationRunConfig(
    evaluation_run_id="eval-2026-test-01",
    provider="fashn",
    model="tryon-v1.6",
    model_version="2026.1",
    provider_api_version="v1",
    configuration_version="vto-cfg-01",
    preprocessing_version="prep-01",
    policy_version="policy-01",
    prompt_version="default",
    spending_ceiling_usd=50.0,
    started_at=datetime.now(UTC),
)


def make_pair(
    pair_id: str = "pair-001",
    eligible: bool = True,
    category: str = "tshirts",
    expected_outcome: ExpectedOutcome = ExpectedOutcome.INFERENCE,
) -> EvaluationPair:
    return EvaluationPair(
        pair_id=pair_id,
        dataset_version="vto-benchmark-1.0",
        participant_id="pseudo-1",
        shopper_asset_id=uuid.uuid4(),
        garment_asset_id=uuid.uuid4(),
        canonical_product_id=uuid.uuid4(),
        garment_category=category,
        permission_record_id="perm-1",
        eligible_for_live_provider=eligible,
        expected_outcome=expected_outcome,
    )


@pytest.mark.asyncio
async def test_runner_executes_eligible_pair():
    """EVAL-001: Eligible pair executes via VTO service and captures results."""
    mock_vto = AsyncMock()
    mock_result = EvaluationItemResult(
        pair_id="pair-001",
        evaluation_run_id="eval-2026-test-01",
        input_validation_status="PASSED",
        job_id="job-123",
        job_status="COMPLETED",
        provider_status="COMPLETED",
        inference_duration_ms=4200,
        end_to_end_duration_ms=5800,
        cost_usd=Decimal("0.0750"),
        output_storage_uri="s3://eval/res.jpg",
    )
    mock_vto.execute_evaluation_job.return_value = mock_result

    runner = TryOnEvaluationRunner(vto_service=mock_vto)
    pair = make_pair()
    res = await runner.run_pair(pair, SAMPLE_RUN_CONFIG)

    assert res.job_status == "COMPLETED"
    assert res.inference_duration_ms == 4200
    mock_vto.execute_evaluation_job.assert_called_once_with(pair, SAMPLE_RUN_CONFIG)


@pytest.mark.asyncio
async def test_runner_blocks_pair_without_permission():
    """EVAL-002: Pair lacking permissions is blocked before calling VTO service."""
    mock_vto = AsyncMock()
    mock_perm = AsyncMock()
    mock_perm.verify_pair_permissions.return_value = False

    runner = TryOnEvaluationRunner(vto_service=mock_vto, permission_service=mock_perm)
    pair = make_pair()
    res = await runner.run_pair(pair, SAMPLE_RUN_CONFIG)

    assert res.input_validation_status == "BLOCKED"
    assert res.rejection_reason == "PERMISSION_DENIED_OR_EXPIRED"
    mock_vto.execute_evaluation_job.assert_not_called()


@pytest.mark.asyncio
async def test_runner_intercepts_negative_case():
    """EVAL-003: Negative/ineligible pair is intercepted as REJECTED without calling provider."""
    mock_vto = AsyncMock()
    runner = TryOnEvaluationRunner(vto_service=mock_vto)

    pair = make_pair(eligible=False, expected_outcome=ExpectedOutcome.REJECT_INPUT)
    res = await runner.run_pair(pair, SAMPLE_RUN_CONFIG)

    assert res.input_validation_status == "REJECTED"
    assert res.rejection_reason == "INELIGIBLE_INPUT_OR_UNSUPPORTED_CATEGORY"
    mock_vto.execute_evaluation_job.assert_not_called()


def test_benchmark_summary_calculation_and_percentiles():
    """EVAL-004 & EVAL-005: Aggregates metrics, percentiles, and category breakdown."""
    pairs = [
        make_pair(pair_id="p1", category="tshirts"),
        make_pair(pair_id="p2", category="tshirts"),
        make_pair(pair_id="p3", category="basic_kurtas"),
        make_pair(pair_id="p4", eligible=False, expected_outcome=ExpectedOutcome.REJECT_INPUT),
    ]

    results = [
        EvaluationItemResult(
            pair_id="p1",
            evaluation_run_id="run-1",
            input_validation_status="PASSED",
            job_status="COMPLETED",
            inference_duration_ms=3000,
            cost_usd=Decimal("0.0750"),
        ),
        EvaluationItemResult(
            pair_id="p2",
            evaluation_run_id="run-1",
            input_validation_status="PASSED",
            job_status="COMPLETED",
            inference_duration_ms=4000,
            cost_usd=Decimal("0.0750"),
        ),
        EvaluationItemResult(
            pair_id="p3",
            evaluation_run_id="run-1",
            input_validation_status="PASSED",
            job_status="FAILED",
            inference_duration_ms=5000,
            cost_usd=Decimal("0.0750"),
        ),
        EvaluationItemResult(
            pair_id="p4",
            evaluation_run_id="run-1",
            input_validation_status="REJECTED",
            job_status="NOT_SUBMITTED",
            cost_usd=Decimal("0.0000"),
        ),
    ]

    summary = TryOnEvaluationRunner.calculate_summary(results, "run-1", pairs)

    assert summary.total_pairs == 4
    assert summary.accepted_pairs == 3
    assert summary.rejected_inputs == 1
    assert summary.completed_jobs == 2
    assert summary.failed_jobs == 1
    # 2 completed out of 3 accepted = 66.67%
    assert summary.job_success_rate == 66.67
    assert summary.input_rejection_accuracy == 100.0
    assert summary.p50_inference_duration_ms == 4000.0
    assert summary.total_spend_usd == Decimal("0.2250")
    assert "tshirts" in summary.category_breakdown
    assert summary.category_breakdown["tshirts"]["completed"] == 2
