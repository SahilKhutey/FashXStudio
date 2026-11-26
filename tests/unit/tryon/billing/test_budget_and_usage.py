"""Unit tests for budget management, usage ledger idempotency, and anomaly monitoring (Phase 07.6).

Covers BUDGET-001 through BUDGET-006, USAGE-001 through USAGE-003, and MONITOR-001 through MONITOR-002.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from fashx.tryon.billing.budget_service import (
    BudgetExceededError,
    BudgetScope,
    ReservationStatus,
    TryOnBudgetService,
)
from fashx.tryon.billing.cost_service import (
    TryOnCostService,
)
from fashx.tryon.billing.usage import (
    OperationStatus,
    ProviderOperation,
    ProviderUsageRecord,
    TryOnProviderUsageService,
)
from fashx.tryon.monitoring.anomaly_detection import (
    BudgetAlertLevel,
    TryOnAnomalyDetector,
)

SAMPLE_JOB_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


class MockBudget:
    def __init__(self, hard_limit: Decimal = Decimal("100.0000")):
        self.id = uuid.uuid4()
        self.scope_type = "PLATFORM"
        self.scope_id = "GLOBAL"
        self.period = "DAILY"
        self.period_start = datetime.now(UTC)
        self.period_end = datetime.now(UTC)
        self.hard_limit_amount = hard_limit
        self.current_spend_usd = Decimal("0.0000")
        self.reserved_spend_usd = Decimal("0.0000")
        self.status = "ACTIVE"
        self.updated_at = datetime.now(UTC)


class MockReservation:
    def __init__(self, budget_id: uuid.UUID, amount: Decimal):
        self.id = uuid.uuid4()
        self.budget_id = budget_id
        self.tryon_job_id = SAMPLE_JOB_ID
        self.reserved_amount_usd = amount
        self.status = "RESERVED"
        self.committed_amount_usd = None
        self.expires_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


@pytest.mark.asyncio
async def test_budget_reservation_within_limit_succeeds():
    """BUDGET-001: Reserving an amount within budget limits succeeds and updates reserved spend."""
    session = AsyncMock()
    budget = MockBudget(hard_limit=Decimal("50.0000"))

    # Mock get_or_create and with_for_update queries
    exec_result = MagicMock()
    exec_result.scalar_one.return_value = budget
    exec_result.scalar_one_or_none.return_value = budget
    session.execute.return_value = exec_result

    service = TryOnBudgetService(session)
    result = await service.reserve_budget(
        tryon_job_id=SAMPLE_JOB_ID,
        scope_type=BudgetScope.PLATFORM,
        scope_id="GLOBAL",
        amount=Decimal("0.0750"),
    )

    assert result.success is True
    assert result.reserved_amount == Decimal("0.0750")
    assert budget.reserved_spend_usd == Decimal("0.0750")


@pytest.mark.asyncio
async def test_budget_reservation_exceeding_limit_raises():
    """BUDGET-002: Requesting more than available budget raises BudgetExceededError."""
    session = AsyncMock()
    budget = MockBudget(hard_limit=Decimal("1.0000"))
    budget.current_spend_usd = Decimal("0.9500")

    exec_result = MagicMock()
    exec_result.scalar_one.return_value = budget
    exec_result.scalar_one_or_none.return_value = budget
    session.execute.return_value = exec_result

    service = TryOnBudgetService(session)
    # 0.9500 + 0.1000 = 1.0500 > 1.0000 limit
    with pytest.raises(BudgetExceededError) as exc_info:
        await service.reserve_budget(
            tryon_job_id=SAMPLE_JOB_ID,
            scope_type=BudgetScope.PLATFORM,
            scope_id="GLOBAL",
            amount=Decimal("0.1000"),
        )

    err = exc_info.value
    assert err.scope_type == "PLATFORM"
    assert err.hard_limit == Decimal("1.0000")


@pytest.mark.asyncio
async def test_commit_reservation():
    """BUDGET-004: Committing a reservation debits reserved and credits current spend."""
    session = AsyncMock()
    budget = MockBudget(hard_limit=Decimal("100.0000"))
    budget.reserved_spend_usd = Decimal("0.0750")
    reservation = MockReservation(budget.id, Decimal("0.0750"))

    # Query returns reservation, then budget
    exec_res_res = MagicMock()
    exec_res_res.scalar_one_or_none.return_value = reservation
    exec_budget_res = MagicMock()
    exec_budget_res.scalar_one.return_value = budget

    session.execute.side_effect = [exec_res_res, exec_budget_res]

    service = TryOnBudgetService(session)
    await service.commit_reservation(reservation.id, actual_cost=Decimal("0.0750"))

    assert reservation.status == ReservationStatus.COMMITTED.value
    assert reservation.committed_amount_usd == Decimal("0.0750")
    assert budget.reserved_spend_usd == Decimal("0.0000")
    assert budget.current_spend_usd == Decimal("0.0750")


@pytest.mark.asyncio
async def test_release_reservation():
    """BUDGET-005: Releasing a reservation restores reserved spend without charging."""
    session = AsyncMock()
    budget = MockBudget(hard_limit=Decimal("100.0000"))
    budget.reserved_spend_usd = Decimal("0.0750")
    reservation = MockReservation(budget.id, Decimal("0.0750"))

    exec_res_res = MagicMock()
    exec_res_res.scalar_one_or_none.return_value = reservation
    exec_budget_res = MagicMock()
    exec_budget_res.scalar_one.return_value = budget

    session.execute.side_effect = [exec_res_res, exec_budget_res]

    service = TryOnBudgetService(session)
    await service.release_reservation(reservation.id, reason="Job cancelled by shopper")

    assert reservation.status == ReservationStatus.RELEASED.value
    assert budget.reserved_spend_usd == Decimal("0.0000")
    assert budget.current_spend_usd == Decimal("0.0000")


@pytest.mark.asyncio
async def test_usage_ledger_recording_and_idempotency():
    """USAGE-001 & USAGE-002: Ledger records usage and deduplicates identical provider requests."""
    session = AsyncMock()

    # First call: no existing record found
    exec_res_first = MagicMock()
    exec_res_first.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_res_first

    service = TryOnProviderUsageService(session)
    record = ProviderUsageRecord(
        provider="fashn",
        operation=ProviderOperation.SUBMIT,
        status=OperationStatus.SUCCESS,
        tryon_job_id=SAMPLE_JOB_ID,
        provider_request_id="req_fashn_abc123",
        units_consumed=Decimal("1.0"),
        unit_cost_usd=Decimal("0.0750"),
    )
    usage = await service.record_usage(record)
    assert usage.total_cost_usd == Decimal("0.0750")

    # Second call with same provider_request_id returns existing record without inserting
    exec_res_second = MagicMock()
    exec_res_second.scalar_one_or_none.return_value = usage
    session.execute.return_value = exec_res_second

    dup_usage = await service.record_usage(record)
    assert dup_usage.id == usage.id


def test_cost_estimation_and_savings():
    """USAGE-003: Cost service resolves correct pricing and calculates savings."""
    session = AsyncMock()
    service = TryOnCostService(session)

    unit_cost = service.get_unit_cost("fashn")
    assert unit_cost == Decimal("0.0750")

    sub_cost = service.estimate_submission_cost("fashn", units=Decimal("2.0"))
    assert sub_cost == Decimal("0.1500")

    savings = service.estimate_cache_savings(hit_count=100, provider="fashn")
    assert savings == Decimal("7.5000")


def test_anomaly_detector_budget_thresholds():
    """MONITOR-001: Anomaly detector triggers WARNING at 70%, CRITICAL at 90%, EXCEEDED at 100%."""
    detector = TryOnAnomalyDetector()

    # Normal (< 70%)
    res_normal = detector.evaluate_budget(
        current_spend_usd=Decimal("50.00"),
        reserved_spend_usd=Decimal("10.00"),
        hard_limit_amount=Decimal("100.00"),
    )
    assert res_normal.alert_level == BudgetAlertLevel.NORMAL
    assert res_normal.utilization_pct == Decimal("60.00")

    # Warning (>= 70%)
    res_warn = detector.evaluate_budget(
        current_spend_usd=Decimal("65.00"),
        reserved_spend_usd=Decimal("10.00"),
        hard_limit_amount=Decimal("100.00"),
    )
    assert res_warn.alert_level == BudgetAlertLevel.WARNING
    assert res_warn.utilization_pct == Decimal("75.00")

    # Critical (>= 90%)
    res_crit = detector.evaluate_budget(
        current_spend_usd=Decimal("85.00"),
        reserved_spend_usd=Decimal("7.00"),
        hard_limit_amount=Decimal("100.00"),
    )
    assert res_crit.alert_level == BudgetAlertLevel.CRITICAL
    assert res_crit.utilization_pct == Decimal("92.00")

    # Exceeded (>= 100%)
    res_exceeded = detector.evaluate_budget(
        current_spend_usd=Decimal("95.00"),
        reserved_spend_usd=Decimal("10.00"),
        hard_limit_amount=Decimal("100.00"),
    )
    assert res_exceeded.alert_level == BudgetAlertLevel.EXCEEDED
    assert res_exceeded.utilization_pct == Decimal("105.00")


def test_anomaly_detector_spend_velocity():
    """MONITOR-002: Detects 3x spend acceleration over baseline."""
    detector = TryOnAnomalyDetector()

    # 10 USD baseline vs 15 USD recent -> 1.5x (Normal)
    assert not detector.detect_spend_velocity_surge(
        recent_window_spend=Decimal("15.00"),
        baseline_window_spend=Decimal("10.00"),
    )

    # 10 USD baseline vs 35 USD recent -> 3.5x (Surge)
    assert detector.detect_spend_velocity_surge(
        recent_window_spend=Decimal("35.00"),
        baseline_window_spend=Decimal("10.00"),
    )
