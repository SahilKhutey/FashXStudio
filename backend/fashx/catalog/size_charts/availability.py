"""Variant availability and inventory snapshot service for Phase 08.1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from .enums import AvailabilityStatus
from .freshness import FreshnessPolicy
from .schemas import ProductVariantAvailability, VariantStockItem


class VariantAvailabilityService:
    """Manages purchasable size/colour variant availability and inventory snapshots."""

    def __init__(self, session_or_db: Any = None) -> None:
        self.session = session_or_db
        # In-memory store for unit test execution and fallback
        self._variants: dict[str, dict[str, Any]] = {}
        self._product_index: dict[str, list[str]] = {}
        self._snapshot_history: list[dict[str, Any]] = []

    def ingest_inventory_snapshot(
        self,
        *,
        merchant_product_id: str | UUID,
        variant_id: str,
        size_label: str,
        availability_status: AvailabilityStatus | str | None = None,
        status: AvailabilityStatus | str | None = None,
        colour_label: str | None = None,
        sku: str | None = None,
        observed_at: datetime | None = None,
        source_updated_at: datetime | None = None,
    ) -> VariantStockItem:
        """Record a verified inventory observation for a merchant product variant.

        Rules:
        1. TAKEDOWN and DELISTED states cannot be overwritten by ordinary inventory sync.
        2. Unknown stock is recorded as UNKNOWN, never as OUT_OF_STOCK.
        3. Timestamps are stored in UTC.
        """
        now = observed_at or datetime.now(UTC)
        raw_status = status or availability_status or AvailabilityStatus.UNKNOWN
        status_enum = (
            raw_status
            if isinstance(raw_status, AvailabilityStatus)
            else AvailabilityStatus(str(raw_status).upper())
        )
        prod_id_str = str(merchant_product_id)

        existing = self._variants.get(variant_id)
        if existing:
            current_status = existing["availability_status"]
            # Protection: normal sync cannot undo legal takedown or delisting
            if current_status in (
                AvailabilityStatus.TAKEDOWN,
                AvailabilityStatus.DELISTED,
            ) and status_enum not in (
                AvailabilityStatus.TAKEDOWN,
                AvailabilityStatus.DELISTED,
            ):
                status_enum = current_status

        record = {
            "variant_id": variant_id,
            "merchant_product_id": prod_id_str,
            "size_label": size_label,
            "colour_label": colour_label,
            "sku": sku,
            "availability_status": status_enum,
            "observed_at": now,
            "source_updated_at": source_updated_at,
        }

        self._variants[variant_id] = record
        if variant_id not in self._product_index.get(prod_id_str, []):
            self._product_index.setdefault(prod_id_str, []).append(variant_id)

        self._snapshot_history.append(
            {
                "snapshot_id": f"snap_{len(self._snapshot_history) + 1}",
                "variant_id": variant_id,
                "status": status_enum,
                "observed_at": now,
            }
        )

        is_stale, effective_status = FreshnessPolicy.evaluate_inventory_freshness(
            now, observed_status=status_enum
        )

        return VariantStockItem(
            variant_id=variant_id,
            size_label=size_label,
            colour_label=colour_label,
            sku=sku,
            status=effective_status,
            is_stale=is_stale,
            observed_at=now,
        )

    def get_variant_availability(
        self, merchant_product_id: str | UUID, variant_id: str
    ) -> VariantStockItem | None:
        """Retrieve availability for an individual variant evaluated against freshness."""
        data = self._variants.get(variant_id)
        if not data:
            return None

        is_stale, effective_status = FreshnessPolicy.evaluate_inventory_freshness(
            data["observed_at"], observed_status=data["availability_status"]
        )
        return VariantStockItem(
            variant_id=data["variant_id"],
            size_label=data["size_label"],
            colour_label=data.get("colour_label"),
            sku=data.get("sku"),
            status=effective_status,
            is_stale=is_stale,
            observed_at=data["observed_at"],
        )

    def get_product_availability(
        self, merchant_product_id: str | UUID
    ) -> ProductVariantAvailability:
        """Retrieve aggregate availability across all variants of a merchant product."""
        prod_id_str = str(merchant_product_id)
        variant_ids = self._product_index.get(prod_id_str, [])
        variants_out: list[VariantStockItem] = []

        has_in_stock = False
        all_out_of_stock = True if variant_ids else False

        for vid in variant_ids:
            v = self.get_variant_availability(prod_id_str, vid)
            if v:
                variants_out.append(v)
                if v.status in (AvailabilityStatus.IN_STOCK, AvailabilityStatus.LOW_STOCK):
                    has_in_stock = True
                if v.status != AvailabilityStatus.OUT_OF_STOCK:
                    all_out_of_stock = False

        overall_status = AvailabilityStatus.UNKNOWN
        if has_in_stock:
            overall_status = AvailabilityStatus.IN_STOCK
        elif all_out_of_stock:
            overall_status = AvailabilityStatus.OUT_OF_STOCK

        p_uuid = merchant_product_id if isinstance(merchant_product_id, UUID) else UUID(prod_id_str)
        return ProductVariantAvailability(
            merchant_product_id=p_uuid,
            overall_status=overall_status,
            variants=variants_out,
            last_checked_at=datetime.now(UTC),
        )
