"""Provider usage ledger and cost accounting service.

Tracks every interaction with external inference providers (e.g. FASHN API):
1. Submissions (paid credit expenditure)
2. Polling status checks
3. Result image downloads
4. Ambiguous submissions (SUBMISSION_UNKNOWN)

Enforces strict idempotency per (provider, provider_request_id, operation)
to guarantee accurate financial auditing and prevent double-counting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProviderOperation(str, Enum):
    SUBMIT = "SUBMIT"
    POLL = "POLL"
    DOWNLOAD = "DOWNLOAD"
    OTHER = "OTHER"


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


@dataclass
class ProviderUsageRecord:
    """Input payload representing a provider operation to record in the ledger."""

    provider: str
    operation: ProviderOperation
    status: OperationStatus
    tryon_job_id: UUID | None = None
    provider_model: str | None = None
    provider_request_id: str | None = None
    units_consumed: Decimal = Decimal("1.0")
    unit_cost_usd: Decimal = Decimal("0.0")
    total_cost_usd: Decimal | None = None
    currency: str = "USD"
    latency_ms: int | None = None
    http_status: int | None = None
    raw_usage_metadata: dict[str, Any] = field(default_factory=dict)

    def compute_total_cost(self) -> Decimal:
        """Compute total cost if not explicitly supplied."""
        if self.total_cost_usd is not None:
            return self.total_cost_usd
        return (self.units_consumed * self.unit_cost_usd).quantize(Decimal("0.0001"))


class TryOnProviderUsageService:
    """Manages recording and retrieval of provider usage ledger records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_usage(self, record: ProviderUsageRecord) -> Any:
        """Record a provider operation idempotently."""
        from database.models.tryon import TryOnProviderUsage

        total_cost = record.compute_total_cost()

        # Idempotency check if provider_request_id is known
        if record.provider_request_id:
            stmt = select(TryOnProviderUsage).where(
                TryOnProviderUsage.provider == record.provider.lower().strip(),
                TryOnProviderUsage.provider_request_id == record.provider_request_id.strip(),
                TryOnProviderUsage.operation == record.operation.value,
            )
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                logger.info(
                    "Duplicate provider usage record detected for %s/%s/%s (existing ID: %s)",
                    record.provider,
                    record.provider_request_id,
                    record.operation.value,
                    existing.id,
                )
                # Update status/latency if improved
                if (
                    existing.status == OperationStatus.UNKNOWN.value
                    and record.status != OperationStatus.UNKNOWN
                ):
                    existing.status = record.status.value
                    if record.latency_ms is not None:
                        existing.latency_ms = record.latency_ms
                    if record.http_status is not None:
                        existing.http_status = record.http_status
                    await self.session.flush()
                return existing

        usage = TryOnProviderUsage(
            tryon_job_id=record.tryon_job_id,
            provider=record.provider.lower().strip(),
            provider_model=record.provider_model,
            provider_request_id=record.provider_request_id.strip()
            if record.provider_request_id
            else None,
            operation=record.operation.value,
            status=record.status.value,
            units_consumed=record.units_consumed,
            unit_cost_usd=record.unit_cost_usd,
            total_cost_usd=total_cost,
            currency=record.currency.upper().strip(),
            latency_ms=record.latency_ms,
            http_status=record.http_status,
            raw_usage_metadata=record.raw_usage_metadata,
        )
        self.session.add(usage)
        await self.session.flush()

        logger.info(
            "Recorded provider usage: %s %s -> %s (Cost: %s %s, Job: %s)",
            record.provider,
            record.operation.value,
            record.status.value,
            total_cost,
            record.currency,
            record.tryon_job_id,
        )
        return usage

    async def get_job_usage(self, tryon_job_id: UUID) -> list[Any]:
        """Fetch all provider ledger records associated with a specific job."""
        from database.models.tryon import TryOnProviderUsage

        stmt = (
            select(TryOnProviderUsage)
            .where(TryOnProviderUsage.tryon_job_id == tryon_job_id)
            .order_by(TryOnProviderUsage.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_total_cost_for_job(self, tryon_job_id: UUID) -> Decimal:
        """Calculate the total realized USD expenditure for a job across all attempts."""
        from database.models.tryon import TryOnProviderUsage

        stmt = select(func.coalesce(func.sum(TryOnProviderUsage.total_cost_usd), 0)).where(
            TryOnProviderUsage.tryon_job_id == tryon_job_id
        )
        res = await self.session.execute(stmt)
        val = res.scalar_one()
        return Decimal(str(val)).quantize(Decimal("0.0001"))
