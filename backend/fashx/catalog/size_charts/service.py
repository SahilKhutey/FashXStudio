"""Service governing merchant-sourced size charts, verification provenance, and freshness."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fashx.catalog.size_charts.availability import VariantAvailabilityService
from fashx.catalog.size_charts.enums import (
    AvailabilityStatus,
    ChangeEventType,
    MappingStatus,
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.errors import (
    SizeChartValidationError,
)
from fashx.catalog.size_charts.fingerprint import compute_size_chart_fingerprint
from fashx.catalog.size_charts.freshness import FreshnessPolicy
from fashx.catalog.size_charts.measurement_fields import FIELD_DEFINITIONS
from fashx.catalog.size_charts.repository import SizeChartRepository
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    ProductSizeChartResponse,
    ProductVariantAvailability,
    SizeChartRevisionCreate,
    SizeChartRevisionSummary,
    SizeChartRow,
    SizeChartRowResponse,
    SizeChartUnavailableResponse,
    SizeMeasurementResponse,
    SizeSystemRef,
    SourceProvenance,
    VariantStockItem,
)
from fashx.catalog.size_charts.size_systems import SYSTEMS, map_size_label
from fashx.catalog.size_charts.units import normalize_to_cm
from fashx.catalog.size_charts.validation import validate_chart

# Re-export SizeChartValidationError for backward compatibility
__all__ = ["SizeChartService", "SizeChartValidationError"]


class SizeChartService:
    """Service governing merchant-sourced size charts, verification provenance, and freshness."""

    DEFAULT_STALE_DAYS = 90

    def __init__(
        self,
        session_or_db: Any = None,
        repository: SizeChartRepository | None = None,
        availability_service: VariantAvailabilityService | None = None,
    ) -> None:
        self.session = session_or_db
        self.repo = repository or SizeChartRepository(session_or_db)
        self.availability_service = availability_service or VariantAvailabilityService()

    # -------------------------------------------------------------------------
    # Backward compatibility methods (Phase 07.8)
    # -------------------------------------------------------------------------

    @staticmethod
    def convert_to_cm(value: Decimal, unit: MeasurementUnit | str) -> Decimal:
        """Deterministically normalize physical measurements to centimeters."""
        u = unit if isinstance(unit, MeasurementUnit) else MeasurementUnit(unit)
        return normalize_to_cm(value, u)

    def validate_and_normalize_chart(
        self,
        *,
        merchant_id: str | UUID,
        merchant_product_id: str,
        merchant_name: str,
        basis: str | MeasurementBasis,
        unit: str | MeasurementUnit,
        source_reference: str,
        source_revision: str,
        rows: list[dict[str, Any] | SizeChartRow],
        canonical_garment_id: str | UUID | None = None,
        last_verified_at: datetime | None = None,
        chart_id: str | None = None,
    ) -> MerchantSizeChartResponse:
        """Validate merchant size chart ingestion (backward compatible)."""
        try:
            basis_enum = MeasurementBasis(basis)
        except (ValueError, TypeError):
            raise SizeChartValidationError(
                f"Invalid or missing measurement basis: '{basis}'. Must be 'BODY' or 'GARMENT'."
            )

        try:
            unit_enum = MeasurementUnit(unit)
        except (ValueError, TypeError):
            raise SizeChartValidationError(
                f"Invalid or missing measurement unit: '{unit}'. Must be 'CM' or 'INCH'."
            )

        if not source_reference or not str(source_reference).strip():
            raise SizeChartValidationError("Source reference is required for provenance tracking.")

        if not merchant_product_id or not str(merchant_product_id).strip():
            raise SizeChartValidationError("Merchant product ID is required.")

        parsed_rows: list[SizeChartRow] = []
        seen_sizes: set[str] = set()

        for idx, r in enumerate(rows):
            try:
                if isinstance(r, SizeChartRow):
                    row_obj = r
                else:
                    row_obj = SizeChartRow(**r)
            except Exception as e:
                raise SizeChartValidationError(
                    f"Row {idx} contains non-positive measurement or invalid data: {e}"
                ) from e

            size_label = row_obj.merchant_size.strip().upper()
            if not size_label:
                raise SizeChartValidationError(f"Row {idx}: merchant_size cannot be empty.")
            if size_label in seen_sizes:
                raise SizeChartValidationError(
                    f"Duplicate size row '{size_label}' in size chart. Conflicting rows prohibited."
                )
            seen_sizes.add(size_label)

            meas_values = [
                row_obj.chest,
                row_obj.waist,
                row_obj.hip,
                row_obj.length,
                row_obj.shoulder,
                row_obj.inseam,
            ]
            valid_measurements = [v for v in meas_values if v is not None]
            if not valid_measurements and not row_obj.additional_measurements:
                raise SizeChartValidationError(
                    f"Size '{size_label}' contains no measurements. Each row must have valid dimension data."
                )

            for val in valid_measurements:
                if val <= 0:
                    raise SizeChartValidationError(
                        f"Size '{size_label}' has non-positive measurement {val}. Must be > 0."
                    )

            parsed_rows.append(row_obj)

        if not parsed_rows:
            raise SizeChartValidationError("Size chart must contain at least one size row.")

        now = datetime.now(UTC)
        verified_at = last_verified_at or now
        is_stale = False
        status_enum = SizeChartStatus.VERIFIED

        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=UTC)

        if now - verified_at > timedelta(days=self.DEFAULT_STALE_DAYS):
            is_stale = True
            status_enum = SizeChartStatus.STALE

        return MerchantSizeChartResponse(
            chart_id=chart_id or f"sc_{merchant_id}_{merchant_product_id}",
            merchant_id=str(merchant_id),
            merchant_name=merchant_name,
            merchant_product_id=str(merchant_product_id),
            canonical_garment_id=str(canonical_garment_id) if canonical_garment_id else None,
            basis=basis_enum,
            unit=unit_enum,
            status=status_enum,
            is_stale=is_stale,
            source_reference=source_reference,
            source_revision=source_revision,
            last_verified_at=verified_at,
            rows=parsed_rows,
        )

    def get_unavailable_response(self, product_id: str | UUID) -> SizeChartUnavailableResponse:
        """Deterministic response when no verified chart is available."""
        return SizeChartUnavailableResponse(product_id=str(product_id))

    # -------------------------------------------------------------------------
    # Phase 08.1 Core End-to-End Capabilities
    # -------------------------------------------------------------------------

    async def ingest_size_chart(
        self,
        *,
        merchant_product_id: UUID,
        merchant_id: UUID,
        payload: SizeChartRevisionCreate,
        category: str = "GENERAL",
        verified_at: datetime | None = None,
        allow_auto_quarantine: bool = True,
    ) -> ProductSizeChartResponse:
        """Ingest a versioned size chart submission, validate, fingerprint, and version it."""
        # 1. Validation
        val_result = validate_chart(payload, garment_category=category)
        if not val_result.is_valid:
            if allow_auto_quarantine:
                await self.repo.quarantine_chart(
                    merchant_product_id=merchant_product_id,
                    merchant_id=merchant_id,
                    source_id=payload.source.source_id,
                    source_revision=payload.source.source_revision,
                    raw_payload=payload.model_dump(mode="json"),
                    error_codes=[e.code for e in val_result.errors],
                )
            error_msgs = "; ".join([e.message for e in val_result.errors])
            raise SizeChartValidationError(f"Size chart validation failed: {error_msgs}")

        # 2. Canonical fingerprinting
        fingerprint = compute_size_chart_fingerprint(payload)

        # 3. Check existing container and revisions
        chart = await self.repo.save_chart(
            merchant_product_id=merchant_product_id,
            merchant_id=merchant_id,
            chart_status=SizeChartStatus.AVAILABLE,
        )

        current_rev = await self.repo.get_current_revision(chart.id)
        if current_rev and current_rev.content_fingerprint == fingerprint:
            # Idempotent re-submission of unchanged chart
            await self.repo.log_event(
                chart_id=chart.id,
                merchant_product_id=merchant_product_id,
                event_type=ChangeEventType.NO_OP_UNCHANGED,
                previous_version=current_rev.version,
                new_version=current_rev.version,
                change_summary={"reason": "Content fingerprint matches active revision"},
            )
            return await self._format_response(chart, current_rev)

        next_version = (current_rev.version + 1) if current_rev else 1

        # 4. Normalize rows data
        prepared_rows: list[dict[str, Any]] = []
        for row_idx, r in enumerate(payload.rows):
            meas_list: list[dict[str, Any]] = []
            for m in r.measurements:
                norm_cm = normalize_to_cm(m.original_value, m.original_unit)
                meas_list.append(
                    {
                        "field_code": m.field_code.upper(),
                        "original_value": float(m.original_value),
                        "original_unit": m.original_unit.value,
                        "normalized_value": float(norm_cm),
                        "normalized_unit": "CM",
                    }
                )
            prepared_rows.append(
                {
                    "merchant_size": r.merchant_size.strip().upper(),
                    "sort_order": r.sort_order if r.sort_order is not None else row_idx,
                    "measurements": meas_list,
                }
            )

        # 5. Persist revision
        revision = await self.repo.save_revision(
            chart=chart,
            version=next_version,
            schema_version=payload.schema_version,
            size_system_code=payload.size_system.code,
            measurement_basis=payload.measurement_basis.value,
            default_unit=payload.default_unit.value,
            content_fingerprint=fingerprint,
            source_id=payload.source.source_id,
            source_revision=payload.source.source_revision,
            source_metadata=payload.source.metadata,
            rows_data=prepared_rows,
            retrieved_at=payload.source.retrieved_at,
            verified_at=verified_at or payload.source.verified_at,
        )

        # 6. Audit event logging
        event_type = (
            ChangeEventType.CHART_CREATED if next_version == 1 else ChangeEventType.VERSION_INCREMENTED
        )
        await self.repo.log_event(
            chart_id=chart.id,
            merchant_product_id=merchant_product_id,
            event_type=event_type,
            previous_version=current_rev.version if current_rev else None,
            new_version=next_version,
            change_summary={"fingerprint": fingerprint, "rows_count": len(prepared_rows)},
        )

        if self.session is not None and next_version > 1:
            from fashx.fit.repository import FitRecommendationRepository

            await FitRecommendationRepository(self.session).invalidate_for_chart(
                chart.id, reason="SIZE_CHART_CHANGED"
            )

        return await self._format_response(chart, revision)

    async def get_product_size_chart(
        self,
        merchant_product_id: UUID,
        *,
        target_unit: MeasurementUnit | None = None,
        target_system: str | None = None,
    ) -> ProductSizeChartResponse | None:
        """Fetch the active size chart for a product, optionally formatted with target unit/system."""
        chart = await self.repo.get_chart_by_product_id(merchant_product_id)
        if not chart or chart.chart_status != SizeChartStatus.AVAILABLE.value:
            return None

        current_rev = await self.repo.get_current_revision(chart.id)
        if not current_rev:
            return None

        return await self._format_response(
            chart, current_rev, target_unit=target_unit, target_system=target_system
        )

    async def list_product_revisions(
        self, merchant_product_id: UUID
    ) -> list[SizeChartRevisionSummary]:
        """List historical revisions for a product's size chart."""
        chart = await self.repo.get_chart_by_product_id(merchant_product_id)
        if not chart:
            return []

        revisions = await self.repo.list_revisions(chart.id)
        summaries: list[SizeChartRevisionSummary] = []
        for r in revisions:
            summaries.append(
                SizeChartRevisionSummary(
                    version=r.version,
                    content_fingerprint=r.content_fingerprint,
                    is_current=r.is_current,
                    size_system_code=r.size_system_code,
                    measurement_basis=MeasurementBasis(r.measurement_basis),
                    default_unit=MeasurementUnit(r.default_unit),
                    created_at=r.created_at,
                    source_id=r.source_id,
                    source_revision=r.source_revision,
                )
            )
        return summaries

    async def get_variant_availability(
        self, merchant_product_id: UUID
    ) -> ProductVariantAvailability:
        """Fetch variant availability records for a product."""
        snapshots = await self.repo.get_latest_inventory_snapshots(merchant_product_id)
        items: list[VariantStockItem] = []
        has_available = False

        for s in snapshots:
            status_enum = AvailabilityStatus(s.availability_status)
            is_stale, effective_status = FreshnessPolicy.evaluate_inventory_freshness(
                s.observed_at, status_enum
            )
            if effective_status == AvailabilityStatus.IN_STOCK:
                has_available = True

            items.append(
                VariantStockItem(
                    variant_id=s.variant_id,
                    size_label=s.size_label,
                    colour_label=s.colour_label,
                    sku=s.sku,
                    status=effective_status,
                    is_stale=is_stale,
                    observed_at=s.observed_at,
                )
            )

        product_status = (
            AvailabilityStatus.IN_STOCK if has_available else AvailabilityStatus.UNKNOWN
        )
        if items and not has_available:
            # Check if all are definitively OUT_OF_STOCK
            if all(i.status == AvailabilityStatus.OUT_OF_STOCK for i in items):
                product_status = AvailabilityStatus.OUT_OF_STOCK

        return ProductVariantAvailability(
            merchant_product_id=merchant_product_id,
            overall_status=product_status,
            variants=items,
            last_checked_at=datetime.now(UTC),
        )

    # -------------------------------------------------------------------------
    # Internal response formatter
    # -------------------------------------------------------------------------

    async def _format_response(
        self,
        chart: Any,
        revision: Any,
        *,
        target_unit: MeasurementUnit | None = None,
        target_system: str | None = None,
    ) -> ProductSizeChartResponse:
        """Format an immutable revision into a rich consumer response."""
        is_stale, effective_status = FreshnessPolicy.evaluate_chart_freshness(
            revision.verified_at, SizeChartStatus(chart.chart_status)
        )

        # System resolution
        sys_code = revision.size_system_code
        sys_def = SYSTEMS.get(sys_code)
        display_name = sys_def.display_name if sys_def else sys_code
        mapping_status = MappingStatus.NATIVE

        if target_system and target_system != sys_code:
            # Attempt mapping
            target_def = SYSTEMS.get(target_system)
            if target_def:
                mapping_status = MappingStatus.UNMAPPED

        sys_ref = SizeSystemRef(
            code=sys_code,
            system_type=sys_def.system_type if sys_def else "MERCHANT_PROPRIETARY",
            display_name=display_name,
            mapping_status=mapping_status,
        )

        # Unit selection
        effective_unit = (
            target_unit
            if target_unit is not None
            else MeasurementUnit(revision.default_unit)
        )

        # Format rows
        formatted_rows: list[SizeChartRowResponse] = []
        raw_rows = revision.rows_json or []

        for idx, r in enumerate(raw_rows):
            m_size = r["merchant_size"]
            mapped_size = None
            if target_system and target_system != sys_code:
                mapped_size = map_size_label(m_size, sys_code, target_system)

            measurements_resp: list[SizeMeasurementResponse] = []
            for m in r.get("measurements", []):
                norm_val = Decimal(str(m["normalized_value"]))
                f_code = m["field_code"]
                field_def = FIELD_DEFINITIONS.get(f_code)
                f_name = field_def.display_name if field_def else f_code

                # Value in effective unit
                if effective_unit == MeasurementUnit.INCH:
                    disp_val = (norm_val / Decimal("2.54")).quantize(Decimal("0.01"))
                elif effective_unit == MeasurementUnit.MM:
                    disp_val = (norm_val * Decimal("10.0")).quantize(Decimal("0.01"))
                else:
                    disp_val = norm_val.quantize(Decimal("0.01"))

                measurements_resp.append(
                    SizeMeasurementResponse(
                        field_code=f_code,
                        display_name=f_name,
                        value=disp_val,
                        unit=effective_unit,
                        normalized_cm=norm_val,
                    )
                )

            formatted_rows.append(
                SizeChartRowResponse(
                    merchant_size=m_size,
                    mapped_size=mapped_size,
                    sort_order=r.get("sort_order", idx),
                    measurements=measurements_resp,
                )
            )

        source_prov = SourceProvenance(
            source_id=revision.source_id,
            source_revision=revision.source_revision,
            retrieved_at=revision.retrieved_at or revision.created_at,
            verified_at=revision.verified_at or revision.created_at,
            metadata=revision.source_metadata_json,
        )

        return ProductSizeChartResponse(
            chart_id=chart.id,
            merchant_product_id=chart.merchant_product_id,
            merchant_id=chart.merchant_id,
            version=revision.version,
            content_fingerprint=revision.content_fingerprint,
            size_system=sys_ref,
            measurement_basis=MeasurementBasis(revision.measurement_basis),
            display_unit=effective_unit,
            status=effective_status,
            is_stale=is_stale,
            provenance=source_prov,
            rows=formatted_rows,
            last_verified_at=revision.verified_at or revision.created_at,
        )
