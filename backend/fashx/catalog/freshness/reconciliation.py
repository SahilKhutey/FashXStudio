"""Safe catalog stale-record reconciliation service for full and incremental syncs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CanonicalGarment, IngestRun, MerchantOffer, MerchantProduct
from database.models.catalog_freshness import (
    AvailabilityStatus,
    CatalogTakedownStatus,
    OfferStatus,
    SyncStatus,
)

logger = logging.getLogger(__name__)


class IncompleteSnapshotError(Exception):
    """Raised when reconciliation is attempted on a run that did not complete successfully."""

    pass


@dataclass
class ReconciliationReport:
    ingest_run_id: UUID
    source_id: UUID
    merchant_id: UUID
    seen_count: int
    missing_count: int
    reconciled_offers: int
    skipped_by_takedown: int
    executed_at: datetime


class CatalogReconciliationService:
    """Safely reconciles missing products after a completed full catalog snapshot."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def reconcile_full_snapshot(
        self,
        ingest_run_id: UUID,
        seen_source_product_ids: set[str],
        apply: bool = False,
    ) -> ReconciliationReport:
        """Reconcile unobserved offers after a verified full snapshot.

        Enforces Section 2 & 6.4 rules:
        - Only runs if the ingest run has status 'COMPLETED' or 'OK'.
        - Fails closed on 'RUNNING', 'FAILED', 'PARTIAL', 'ABORTED', or 'REJECTED' runs.
        - Never overrides an active takedown (REQUESTED, PROCESSING, COMPLETED, UNDER_REVIEW).
        - Marks missing offers as SOURCE_MISSING and OUT_OF_STOCK without deleting records or price history.
        """
        # 1. Fetch IngestRun
        stmt = select(IngestRun).where(IngestRun.id == ingest_run_id)
        run = (await self.session.scalars(stmt)).first()
        if run is None:
            raise ValueError(f"IngestRun '{ingest_run_id}' not found")

        # Invariant: run status must be strictly COMPLETED or OK
        normalized_status = (run.status or "").upper()
        if normalized_status not in {"COMPLETED", "OK"}:
            raise IncompleteSnapshotError(
                f"Cannot reconcile stale offers: ingest run '{ingest_run_id}' status is '{run.status}'. "
                f"Only COMPLETED full snapshot runs allow stale reconciliation."
            )

        source_id = run.source_id
        merchant_id = run.merchant_id

        # 2. Query all existing offers for this source/merchant
        offer_stmt = (
            select(MerchantOffer)
            .join(
                MerchantProduct,
                (MerchantProduct.merchant_id == MerchantOffer.merchant_id)
                & (MerchantProduct.source_product_id == MerchantOffer.source_product_id),
            )
            .where(
                MerchantProduct.source_id == source_id,
            )
        )
        if merchant_id:
            offer_stmt = offer_stmt.where(MerchantOffer.merchant_id == merchant_id)

        offers = list((await self.session.scalars(offer_stmt)).all())

        missing_count = 0
        reconciled_count = 0
        skipped_takedowns = 0
        now = datetime.now(UTC)

        for offer in offers:
            if offer.source_product_id in seen_source_product_ids:
                # Offer was seen in this run; ensure sync status is current
                offer.sync_status = SyncStatus.CURRENT
                offer.last_seen_at = now
                continue

            # Offer was NOT seen in the full snapshot
            missing_count += 1

            # Invariant: Never override an active takedown
            if offer.takedown_status in {
                CatalogTakedownStatus.REQUESTED,
                CatalogTakedownStatus.PROCESSING,
                CatalogTakedownStatus.COMPLETED,
                CatalogTakedownStatus.UNDER_REVIEW,
            }:
                skipped_takedowns += 1
                continue

            # Mark offer missing and out of stock
            offer.status = OfferStatus.OUT_OF_STOCK
            offer.availability = AvailabilityStatus.OUT_OF_STOCK
            offer.sync_status = SyncStatus.SOURCE_MISSING
            offer.in_stock = False
            offer.last_changed_at = now
            reconciled_count += 1

            # Update parent CanonicalGarment stock if no other in-stock offers exist
            garment_stmt = select(CanonicalGarment).where(CanonicalGarment.id == offer.garment_id)
            garment = (await self.session.scalars(garment_stmt)).first()
            if garment is not None:
                other_in_stock_stmt = select(MerchantOffer).where(
                    MerchantOffer.garment_id == offer.garment_id,
                    MerchantOffer.id != offer.id,
                    MerchantOffer.in_stock.is_(True),
                )
                has_active = (await self.session.scalars(other_in_stock_stmt)).first()
                if has_active is None:
                    garment.in_stock = False

        if apply:
            await self.session.flush()

        return ReconciliationReport(
            ingest_run_id=ingest_run_id,
            source_id=source_id,
            merchant_id=merchant_id or source_id,
            seen_count=len(seen_source_product_ids),
            missing_count=missing_count,
            reconciled_offers=reconciled_count,
            skipped_by_takedown=skipped_takedowns,
            executed_at=now,
        )
