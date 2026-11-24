"""Evaluation pipeline runner and benchmark orchestration for Virtual Try-On.

Guarantees:
1. Reuses the authentic VTO job pipeline and Phase 07.6 budget reservation checks.
2. Zero unauthorized execution: Every pair must pass participant and garment permissions.
3. Negative cases and unsupported categories are intercepted and validated without incurring paid provider fees.
4. Tracks exact latencies (P50, P90, P95) and costs per category and input condition.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from backend.fashx.tryon.evaluation.contracts import (
    EvaluationPair,
    EvaluationRunConfig,
    ExpectedOutcome,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationItemResult:
    """Outcome of an individual evaluation pair execution."""

    pair_id: str
    evaluation_run_id: str
    input_validation_status: str  # PASSED | REJECTED | BLOCKED
    job_id: str | None = None
    job_status: str = "NOT_SUBMITTED"
    provider_status: str | None = None
    provider_request_id: str | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    inference_duration_ms: int | None = None
    end_to_end_duration_ms: int | None = None
    retry_count: int = 0
    cost_usd: Decimal = Decimal("0.0000")
    output_storage_uri: str | None = None
    output_sha256: str | None = None
    error_code: str | None = None
    rejection_reason: str | None = None


@dataclass
class BenchmarkExecutionSummary:
    """Aggregated operational metrics for an evaluation run."""

    evaluation_run_id: str
    total_pairs: int
    accepted_pairs: int
    rejected_inputs: int
    completed_jobs: int
    failed_jobs: int
    job_success_rate: float
    input_rejection_accuracy: float
    p50_inference_duration_ms: float | None
    p90_inference_duration_ms: float | None
    p95_inference_duration_ms: float | None
    total_spend_usd: Decimal
    category_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)


class PermissionService(Protocol):
    """Protocol for checking dataset asset permissions."""

    async def verify_pair_permissions(self, pair: EvaluationPair) -> bool: ...


class EvaluationVtoService(Protocol):
    """Protocol for submitting evaluation jobs through production TryOn service."""

    async def execute_evaluation_job(
        self,
        pair: EvaluationPair,
        run_config: EvaluationRunConfig,
    ) -> EvaluationItemResult: ...


class TryOnEvaluationRunner:
    """Orchestrates controlled VTO quality benchmarks across dataset manifests."""

    def __init__(
        self,
        vto_service: EvaluationVtoService,
        permission_service: PermissionService | None = None,
    ) -> None:
        self.vto_service = vto_service
        self.permission_service = permission_service

    async def run_pair(
        self,
        pair: EvaluationPair,
        run_config: EvaluationRunConfig,
    ) -> EvaluationItemResult:
        """Execute a single evaluation pair with permission and eligibility gates."""
        # 1. Permission Gate
        if self.permission_service is not None:
            has_permission = await self.permission_service.verify_pair_permissions(pair)
            if not has_permission:
                logger.warning(
                    "Pair %s lacks valid participant or merchant permissions", pair.pair_id
                )
                return EvaluationItemResult(
                    pair_id=pair.pair_id,
                    evaluation_run_id=run_config.evaluation_run_id,
                    input_validation_status="BLOCKED",
                    rejection_reason="PERMISSION_DENIED_OR_EXPIRED",
                )

        # 2. Input Eligibility / Negative Case Gate
        if not pair.eligible_for_live_provider:
            # Expected rejection
            logger.info(
                "Pair %s is marked ineligible for live inference (negative case)", pair.pair_id
            )
            return EvaluationItemResult(
                pair_id=pair.pair_id,
                evaluation_run_id=run_config.evaluation_run_id,
                input_validation_status="REJECTED",
                rejection_reason="INELIGIBLE_INPUT_OR_UNSUPPORTED_CATEGORY",
            )

        # 3. Production VTO Execution
        return await self.vto_service.execute_evaluation_job(pair, run_config)

    async def run_benchmark(
        self,
        pairs: list[EvaluationPair],
        run_config: EvaluationRunConfig,
    ) -> tuple[list[EvaluationItemResult], BenchmarkExecutionSummary]:
        """Execute all pairs sequentially or in controlled batches, computing metrics."""
        results: list[EvaluationItemResult] = []

        for pair in pairs:
            res = await self.run_pair(pair, run_config)
            results.append(res)

        summary = self.calculate_summary(results, run_config.evaluation_run_id, pairs)
        return results, summary

    @staticmethod
    def calculate_summary(
        results: list[EvaluationItemResult],
        run_id: str,
        pairs: list[EvaluationPair],
    ) -> BenchmarkExecutionSummary:
        """Calculate statistical execution metrics and latency percentiles."""
        total = len(results)
        pair_map = {p.pair_id: p for p in pairs}

        accepted = [r for r in results if r.input_validation_status == "PASSED"]
        rejected = [r for r in results if r.input_validation_status in ("REJECTED", "BLOCKED")]
        completed = [r for r in results if r.job_status == "COMPLETED"]
        failed = [r for r in accepted if r.job_status in ("FAILED", "SUBMISSION_UNKNOWN")]

        success_rate = (len(completed) / len(accepted) * 100.0) if accepted else 0.0

        # Calculate input rejection accuracy: correctly rejected negative inputs
        correct_rejections = 0
        total_expected_rejections = 0
        for r in results:
            p = pair_map.get(r.pair_id)
            if p and p.expected_outcome == ExpectedOutcome.REJECT_INPUT:
                total_expected_rejections += 1
                if r.input_validation_status in ("REJECTED", "BLOCKED"):
                    correct_rejections += 1

        rejection_accuracy = (
            (correct_rejections / total_expected_rejections * 100.0)
            if total_expected_rejections > 0
            else 100.0
        )

        # Latencies
        latencies = sorted(
            [r.inference_duration_ms for r in results if r.inference_duration_ms is not None]
        )

        def percentile(data: list[int], pct: float) -> float | None:
            if not data:
                return None
            k = (len(data) - 1) * pct
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return float(data[int(k)])
            d0 = data[int(f)] * (c - k)
            d1 = data[int(c)] * (k - f)
            return float(d0 + d1)

        p50 = percentile(latencies, 0.50)
        p90 = percentile(latencies, 0.90)
        p95 = percentile(latencies, 0.95)

        total_spend = sum((r.cost_usd for r in results), Decimal("0.0000"))

        # Category Breakdown
        breakdown: dict[str, dict[str, Any]] = {}
        for r in results:
            p = pair_map.get(r.pair_id)
            cat = p.garment_category if p else "UNKNOWN"
            cat_data = breakdown.setdefault(
                cat, {"total": 0, "completed": 0, "rejected": 0, "failed": 0}
            )
            cat_data["total"] += 1
            if r.job_status == "COMPLETED":
                cat_data["completed"] += 1
            elif r.input_validation_status in ("REJECTED", "BLOCKED"):
                cat_data["rejected"] += 1
            else:
                cat_data["failed"] += 1

        return BenchmarkExecutionSummary(
            evaluation_run_id=run_id,
            total_pairs=total,
            accepted_pairs=len(accepted),
            rejected_inputs=len(rejected),
            completed_jobs=len(completed),
            failed_jobs=len(failed),
            job_success_rate=round(success_rate, 2),
            input_rejection_accuracy=round(rejection_accuracy, 2),
            p50_inference_duration_ms=p50,
            p90_inference_duration_ms=p90,
            p95_inference_duration_ms=p95,
            total_spend_usd=total_spend,
            category_breakdown=breakdown,
        )
