from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fashx.catalog.size_charts.schemas import (
    MeasurementBasis,
    MeasurementUnit,
    MerchantSizeChartResponse,
    SizeChartRow,
    SizeChartStatus,
    SizeChartUnavailableResponse,
)


class SizeChartValidationError(ValueError):
    """Raised when incoming size chart data fails provenance, unit, or basis invariants."""

    pass


class SizeChartService:
    """Service governing merchant-sourced size charts, verification provenance, and freshness."""

    DEFAULT_STALE_DAYS = 90

    def __init__(self, session_or_db: Any = None) -> None:
        self.session = session_or_db

    @staticmethod
    def convert_to_cm(value: Decimal, unit: MeasurementUnit) -> Decimal:
        """Deterministically normalize physical measurements to centimeters."""
        if unit == MeasurementUnit.INCH:
            return (value * Decimal("2.54")).quantize(Decimal("0.01"))
        return value.quantize(Decimal("0.01"))

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
        """Validate merchant size chart ingestion.

        Rules:
        1. Measurement basis (BODY vs GARMENT) must be explicit.
        2. Measurement unit (CM vs INCH) must be valid.
        3. Sizes must be non-empty and unique.
        4. Numeric measurements must be strictly positive.
        5. Missing charts must NEVER be guessed or filled by AI.
        """
        # Validate basis
        try:
            basis_enum = MeasurementBasis(basis)
        except (ValueError, TypeError):
            raise SizeChartValidationError(
                f"Invalid or missing measurement basis: '{basis}'. Must be 'BODY' or 'GARMENT'."
            )

        # Validate unit
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

        # Process and validate rows
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

            # Check that at least one measurement is provided and all are positive
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

        # Freshness check
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
