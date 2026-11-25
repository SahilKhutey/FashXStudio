"""Repository for persisting and querying product size charts, revisions, and availability."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.size_charts import (
    InventorySnapshotRecord,
    MeasurementFieldDefinitionRecord,
    ProductSizeChartRecord,
    SizeChartEventRecord,
    SizeChartMeasurementRecord,
    SizeChartQuarantineRecord,
    SizeChartRevisionRecord,
    SizeChartRowRecord,
    SizeSystemDefinitionRecord,
)
from fashx.catalog.size_charts.enums import AvailabilityStatus, ChangeEventType, SizeChartStatus


class SizeChartRepository:
    """Data access repository for product size charts, revisions, and inventory snapshots."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        # In-memory store fallback when operating without a DB session (unit tests/mock)
        self._charts: dict[UUID, ProductSizeChartRecord] = {}
        self._revisions: dict[UUID, list[SizeChartRevisionRecord]] = {}
        self._inventory: dict[UUID, list[InventorySnapshotRecord]] = {}
        self._events: list[SizeChartEventRecord] = []
        self._quarantine: list[SizeChartQuarantineRecord] = []
        self._size_systems: dict[str, SizeSystemDefinitionRecord] = {}
        self._field_defs: dict[str, MeasurementFieldDefinitionRecord] = {}

    async def get_chart_by_product_id(self, product_id: UUID) -> ProductSizeChartRecord | None:
        """Fetch the product size chart container for a given merchant product."""
        if self.session is not None:
            stmt = (
                select(ProductSizeChartRecord)
                .where(ProductSizeChartRecord.merchant_product_id == product_id)
                .options(selectinload(ProductSizeChartRecord.revisions))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        return self._charts.get(product_id)

    async def get_current_revision(self, chart_id: UUID) -> SizeChartRevisionRecord | None:
        """Fetch the currently active revision for a chart."""
        if self.session is not None:
            stmt = (
                select(SizeChartRevisionRecord)
                .where(
                    SizeChartRevisionRecord.chart_id == chart_id,
                    SizeChartRevisionRecord.is_current.is_(True),
                )
                .options(
                    selectinload(SizeChartRevisionRecord.rows).selectinload(
                        SizeChartRowRecord.measurements
                    )
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        revs = self._revisions.get(chart_id, [])
        for r in revs:
            if r.is_current:
                return r
        return revs[-1] if revs else None

    async def get_revision_by_version(
        self, chart_id: UUID, version: int
    ) -> SizeChartRevisionRecord | None:
        """Fetch a specific historical revision of a size chart."""
        if self.session is not None:
            stmt = (
                select(SizeChartRevisionRecord)
                .where(
                    SizeChartRevisionRecord.chart_id == chart_id,
                    SizeChartRevisionRecord.version == version,
                )
                .options(
                    selectinload(SizeChartRevisionRecord.rows).selectinload(
                        SizeChartRowRecord.measurements
                    )
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        revs = self._revisions.get(chart_id, [])
        for r in revs:
            if r.version == version:
                return r
        return None

    async def list_revisions(self, chart_id: UUID) -> list[SizeChartRevisionRecord]:
        """List all revisions for a chart in descending order of version."""
        if self.session is not None:
            stmt = (
                select(SizeChartRevisionRecord)
                .where(SizeChartRevisionRecord.chart_id == chart_id)
                .order_by(desc(SizeChartRevisionRecord.version))
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        revs = self._revisions.get(chart_id, [])
        return sorted(revs, key=lambda x: x.version, reverse=True)

    async def save_chart(
        self,
        *,
        merchant_product_id: UUID,
        merchant_id: UUID,
        chart_status: SizeChartStatus = SizeChartStatus.AVAILABLE,
    ) -> ProductSizeChartRecord:
        """Create or return existing product size chart record."""
        existing = await self.get_chart_by_product_id(merchant_product_id)
        if existing:
            return existing

        chart = ProductSizeChartRecord(
            id=uuid4(),
            merchant_product_id=merchant_product_id,
            merchant_id=merchant_id,
            chart_status=chart_status.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        if self.session is not None:
            self.session.add(chart)
            await self.session.flush()
        else:
            self._charts[merchant_product_id] = chart

        return chart

    async def save_revision(
        self,
        *,
        chart: ProductSizeChartRecord,
        version: int,
        schema_version: str,
        size_system_code: str,
        measurement_basis: str,
        default_unit: str,
        content_fingerprint: str,
        source_id: str | None,
        source_revision: str | None,
        source_metadata: dict[str, Any] | None,
        rows_data: list[dict[str, Any]],
        retrieved_at: datetime | None = None,
        verified_at: datetime | None = None,
    ) -> SizeChartRevisionRecord:
        """Store a new immutable size chart revision and update the parent pointer."""
        # Deactivate previous active revisions
        if self.session is not None:
            all_revs = await self.list_revisions(chart.id)
            for r in all_revs:
                if r.is_current:
                    r.is_current = False
        else:
            for r in self._revisions.get(chart.id, []):
                r.is_current = False

        revision = SizeChartRevisionRecord(
            id=uuid4(),
            chart_id=chart.id,
            merchant_product_id=chart.merchant_product_id,
            version=version,
            schema_version=schema_version,
            size_system_code=size_system_code,
            measurement_basis=measurement_basis,
            default_unit=default_unit,
            content_fingerprint=content_fingerprint,
            source_id=source_id,
            source_revision=source_revision,
            source_metadata_json=source_metadata,
            rows_json=rows_data,
            is_current=True,
            retrieved_at=retrieved_at or datetime.now(UTC),
            verified_at=verified_at or datetime.now(UTC),
            created_at=datetime.now(UTC),
        )

        # Build row and measurement records
        row_records: list[SizeChartRowRecord] = []
        for idx, row in enumerate(rows_data):
            row_rec = SizeChartRowRecord(
                id=uuid4(),
                revision_id=revision.id,
                merchant_size=row["merchant_size"],
                sort_order=row.get("sort_order", idx),
            )
            measurements: list[SizeChartMeasurementRecord] = []
            for m in row.get("measurements", []):
                meas_rec = SizeChartMeasurementRecord(
                    id=uuid4(),
                    row_id=row_rec.id,
                    field_code=m["field_code"],
                    original_value=float(m["original_value"]),
                    original_unit=m["original_unit"],
                    normalized_value=float(m["normalized_value"]),
                    normalized_unit=m.get("normalized_unit", "CM"),
                )
                measurements.append(meas_rec)
            row_rec.measurements = measurements
            row_records.append(row_rec)

        revision.rows = row_records
        chart.current_revision_id = revision.id
        chart.updated_at = datetime.now(UTC)

        if self.session is not None:
            self.session.add(revision)
            for rr in row_records:
                self.session.add(rr)
                for mm in rr.measurements:
                    self.session.add(mm)
            await self.session.flush()
        else:
            if chart.id not in self._revisions:
                self._revisions[chart.id] = []
            self._revisions[chart.id].append(revision)

        return revision

    async def log_event(
        self,
        *,
        chart_id: UUID | None,
        merchant_product_id: UUID,
        event_type: ChangeEventType | str,
        previous_version: int | None = None,
        new_version: int | None = None,
        change_summary: dict[str, Any] | None = None,
    ) -> SizeChartEventRecord:
        """Record an event in the audit event log."""
        type_str = event_type.value if isinstance(event_type, ChangeEventType) else str(event_type)
        event = SizeChartEventRecord(
            id=uuid4(),
            chart_id=chart_id,
            merchant_product_id=merchant_product_id,
            event_type=type_str,
            previous_version=previous_version,
            new_version=new_version,
            change_summary_json=change_summary,
            created_at=datetime.now(UTC),
        )
        if self.session is not None:
            self.session.add(event)
            await self.session.flush()
        else:
            self._events.append(event)
        return event

    async def quarantine_chart(
        self,
        *,
        merchant_product_id: UUID,
        merchant_id: UUID,
        source_id: str | None,
        source_revision: str | None,
        raw_payload: dict[str, Any],
        error_codes: list[str],
    ) -> SizeChartQuarantineRecord:
        """Quarantine a rejected size chart submission."""
        record = SizeChartQuarantineRecord(
            id=uuid4(),
            merchant_product_id=merchant_product_id,
            merchant_id=merchant_id,
            source_id=source_id,
            source_revision=source_revision,
            raw_payload_json=raw_payload,
            error_codes_json=error_codes,
            review_status="PENDING",
            created_at=datetime.now(UTC),
        )
        if self.session is not None:
            self.session.add(record)
            await self.session.flush()
        else:
            self._quarantine.append(record)
        return record

    async def save_inventory_snapshot(
        self,
        *,
        variant_id: str,
        merchant_product_id: UUID,
        size_label: str,
        availability_status: AvailabilityStatus | str,
        colour_label: str | None = None,
        sku: str | None = None,
        observed_at: datetime | None = None,
        source_updated_at: datetime | None = None,
    ) -> InventorySnapshotRecord:
        """Record an inventory availability snapshot."""
        status_str = (
            availability_status.value
            if isinstance(availability_status, AvailabilityStatus)
            else str(availability_status)
        )
        record = InventorySnapshotRecord(
            id=uuid4(),
            variant_id=variant_id,
            merchant_product_id=merchant_product_id,
            size_label=size_label,
            colour_label=colour_label,
            sku=sku,
            availability_status=status_str,
            observed_at=observed_at or datetime.now(UTC),
            source_updated_at=source_updated_at,
        )
        if self.session is not None:
            self.session.add(record)
            await self.session.flush()
        else:
            if merchant_product_id not in self._inventory:
                self._inventory[merchant_product_id] = []
            self._inventory[merchant_product_id].append(record)
        return record

    async def get_latest_inventory_snapshots(
        self, merchant_product_id: UUID
    ) -> list[InventorySnapshotRecord]:
        """Get the most recent snapshot per variant for a product."""
        if self.session is not None:
            stmt = (
                select(InventorySnapshotRecord)
                .where(InventorySnapshotRecord.merchant_product_id == merchant_product_id)
                .order_by(desc(InventorySnapshotRecord.observed_at))
            )
            result = await self.session.execute(stmt)
            records = list(result.scalars().all())
        else:
            records = self._inventory.get(merchant_product_id, [])

        latest: dict[str, InventorySnapshotRecord] = {}
        for r in records:
            if r.variant_id not in latest:
                latest[r.variant_id] = r
            elif r.observed_at > latest[r.variant_id].observed_at:
                latest[r.variant_id] = r
        return list(latest.values())


ProductSizeChartRepository = SizeChartRepository
