"""Multi-tier budget management and atomic reservation service.

Guarantees:
1. Strict pre-inference reservation: Before any paid provider call is initiated,
   funds are reserved against Platform, Merchant, and/or User budgets.
2. Race condition protection: Uses database row locking (SELECT ... FOR UPDATE)
   to ensure parallel workers cannot exceed spending limits.
3. Ambiguous submission safety: If provider response is ambiguous (SUBMISSION_UNKNOWN),
   the reservation is retained until explicit reconciliation occurs.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.fashx.tryon.billing.reservations import (
    BudgetExceededError,
    BudgetPeriod,
    BudgetScope,
    BudgetStatus,
    ReservationResult,
    ReservationStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_PLATFORM_DAILY_BUDGET = Decimal("500.0000")
DEFAULT_MERCHANT_DAILY_BUDGET = Decimal("50.0000")
DEFAULT_USER_DAILY_BUDGET = Decimal("5.0000")


class TryOnBudgetService:
    """Coordinates budget enforcement and atomic reservations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_budget(
        self,
        scope_type: BudgetScope,
        scope_id: str,
        period: BudgetPeriod = BudgetPeriod.DAILY,
        default_limit: Decimal | None = None,
    ) -> Any:
        """Fetch active budget for current period or initialize with default limit."""
        from database.models.tryon import TryOnBudget

        now = datetime.now(UTC)
        if period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            limit = default_limit or (
                DEFAULT_PLATFORM_DAILY_BUDGET
                if scope_type == BudgetScope.PLATFORM
                else DEFAULT_MERCHANT_DAILY_BUDGET
                if scope_type == BudgetScope.MERCHANT
                else DEFAULT_USER_DAILY_BUDGET
            )
        else:
            # Monthly
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month
            limit = default_limit or Decimal("5000.0000")

        stmt = select(TryOnBudget).where(
            TryOnBudget.scope_type == scope_type.value,
            TryOnBudget.scope_id == scope_id,
            TryOnBudget.period == period.value,
            TryOnBudget.period_start == start,
        )
        res = await self.session.execute(stmt)
        budget = res.scalar_one_or_none()

        if not budget:
            budget = TryOnBudget(
                scope_type=scope_type.value,
                scope_id=scope_id,
                period=period.value,
                period_start=start,
                period_end=end,
                hard_limit_amount=limit,
                warn_threshold_pct=Decimal("70.00"),
                crit_threshold_pct=Decimal("90.00"),
                current_spend_usd=Decimal("0.0000"),
                reserved_spend_usd=Decimal("0.0000"),
                status=BudgetStatus.ACTIVE.value,
            )
            self.session.add(budget)
            await self.session.flush()

        return budget

    async def reserve_budget(
        self,
        tryon_job_id: UUID,
        scope_type: BudgetScope,
        scope_id: str,
        amount: Decimal,
        period: BudgetPeriod = BudgetPeriod.DAILY,
        timeout_minutes: int = 15,
    ) -> ReservationResult:
        """Atomically reserve funds against a budget using row locking."""
        from database.models.tryon import TryOnBudget, TryOnBudgetReservation

        budget = await self.get_or_create_budget(scope_type, scope_id, period)

        # Lock budget row for update
        stmt = select(TryOnBudget).where(TryOnBudget.id == budget.id).with_for_update()
        res = await self.session.execute(stmt)
        locked_budget = res.scalar_one()

        available = locked_budget.hard_limit_amount - (
            locked_budget.current_spend_usd + locked_budget.reserved_spend_usd
        )

        if amount > available:
            logger.warning(
                "BUDGET EXCEEDED for %s:%s (Requested: %s, Available: %s, Limit: %s)",
                scope_type.value,
                scope_id,
                amount,
                available,
                locked_budget.hard_limit_amount,
            )
            raise BudgetExceededError(
                message=f"Virtual try-on spending limit reached for {scope_type.value}.",
                scope_type=scope_type.value,
                scope_id=scope_id,
                hard_limit=locked_budget.hard_limit_amount,
                current_spend=locked_budget.current_spend_usd,
                reserved_spend=locked_budget.reserved_spend_usd,
                requested_amount=amount,
            )

        # Increment reserved amount
        locked_budget.reserved_spend_usd += amount

        # Create reservation record
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=timeout_minutes)
        reservation = TryOnBudgetReservation(
            budget_id=locked_budget.id,
            tryon_job_id=tryon_job_id,
            reserved_amount_usd=amount,
            status=ReservationStatus.RESERVED.value,
            expires_at=expires_at,
        )
        self.session.add(reservation)
        await self.session.flush()

        logger.info(
            "Reserved %s USD on budget %s for job %s (Total reserved: %s)",
            amount,
            locked_budget.id,
            tryon_job_id,
            locked_budget.reserved_spend_usd,
        )

        return ReservationResult(
            success=True,
            reservation_id=reservation.id,
            budget_id=locked_budget.id,
            reserved_amount=amount,
        )

    async def commit_reservation(
        self,
        reservation_id: UUID,
        actual_cost: Decimal,
    ) -> None:
        """Settle reservation upon completed inference, committing realized spend."""
        from database.models.tryon import TryOnBudget, TryOnBudgetReservation

        res_stmt = (
            select(TryOnBudgetReservation)
            .where(TryOnBudgetReservation.id == reservation_id)
            .with_for_update()
        )
        res_res = await self.session.execute(res_stmt)
        reservation = res_res.scalar_one_or_none()
        if not reservation or reservation.status != ReservationStatus.RESERVED.value:
            logger.warning("Reservation %s not in RESERVED state; skipping commit", reservation_id)
            return

        budget_stmt = (
            select(TryOnBudget).where(TryOnBudget.id == reservation.budget_id).with_for_update()
        )
        b_res = await self.session.execute(budget_stmt)
        budget = b_res.scalar_one()

        # Update budget
        budget.reserved_spend_usd = max(
            Decimal("0.0000"), budget.reserved_spend_usd - reservation.reserved_amount_usd
        )
        budget.current_spend_usd += actual_cost
        budget.updated_at = datetime.now(UTC)

        # Update reservation
        reservation.status = ReservationStatus.COMMITTED.value
        reservation.committed_amount_usd = actual_cost
        reservation.updated_at = datetime.now(UTC)

        await self.session.flush()
        logger.info(
            "Committed reservation %s: spent %s USD (released reserve: %s)",
            reservation_id,
            actual_cost,
            reservation.reserved_amount_usd,
        )

    async def release_reservation(
        self,
        reservation_id: UUID,
        reason: str | None = None,
    ) -> None:
        """Release reservation without expenditure (e.g. job cancelled or failed before dispatch)."""
        from database.models.tryon import TryOnBudget, TryOnBudgetReservation

        res_stmt = (
            select(TryOnBudgetReservation)
            .where(TryOnBudgetReservation.id == reservation_id)
            .with_for_update()
        )
        res_res = await self.session.execute(res_stmt)
        reservation = res_res.scalar_one_or_none()
        if not reservation or reservation.status != ReservationStatus.RESERVED.value:
            return

        budget_stmt = (
            select(TryOnBudget).where(TryOnBudget.id == reservation.budget_id).with_for_update()
        )
        b_res = await self.session.execute(budget_stmt)
        budget = b_res.scalar_one()

        budget.reserved_spend_usd = max(
            Decimal("0.0000"), budget.reserved_spend_usd - reservation.reserved_amount_usd
        )
        budget.updated_at = datetime.now(UTC)

        reservation.status = ReservationStatus.RELEASED.value
        reservation.updated_at = datetime.now(UTC)

        await self.session.flush()
        logger.info(
            "Released reservation %s (%s USD) - Reason: %s",
            reservation_id,
            reservation.reserved_amount_usd,
            reason or "Unspecified",
        )

    async def hold_reservation_for_reconciliation(
        self,
        reservation_id: UUID,
    ) -> None:
        """Hold reservation in case of SUBMISSION_UNKNOWN until provider state is reconciled."""
        from database.models.tryon import TryOnBudgetReservation

        stmt = (
            update(TryOnBudgetReservation)
            .where(TryOnBudgetReservation.id == reservation_id)
            .values(
                status=ReservationStatus.HELD_FOR_RECONCILIATION.value,
                updated_at=datetime.now(UTC),
            )
        )
        await self.session.execute(stmt)
        logger.warning(
            "Reservation %s held for reconciliation due to ambiguous provider response",
            reservation_id,
        )
